"""ShopLite - small web shop used for Lab 3 (monitoring, logging, feature flags, testing)."""
import hashlib
import json
import logging
import os
import random
import socket
import time

from flask import Flask, g, jsonify, render_template, request
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
INSTANCE = os.getenv("APP_INSTANCE", socket.gethostname())
FLAGS_FILE = os.getenv("FLAGS_FILE", os.path.join(os.path.dirname(__file__), "flags.json"))
LOG_FILE = os.getenv("LOG_FILE", "")

PRODUCTS = [
    {"id": 1, "name": "Laptop Stand", "price": 1499},
    {"id": 2, "name": "Wireless Mouse", "price": 799},
    {"id": 3, "name": "USB-C Hub", "price": 2199},
    {"id": 4, "name": "Mechanical Keyboard", "price": 3499},
]

# ---------------- logging (plain text, parsed later by Logstash grok) ----------------
log = logging.getLogger("shoplite")
log.setLevel(logging.INFO)
_fmt = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)s shoplite %(message)s", "%Y-%m-%dT%H:%M:%S")
_h = logging.StreamHandler()
_h.setFormatter(_fmt)
log.addHandler(_h)
if LOG_FILE:
    _fh = logging.FileHandler(LOG_FILE)
    _fh.setFormatter(_fmt)
    log.addHandler(_fh)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

# ---------------- metrics ----------------
REQUESTS = Counter("http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"])
LATENCY = Histogram("http_request_duration_seconds", "Request latency", ["endpoint"],
                    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5))
ORDERS = Counter("shop_orders_total", "Orders placed", ["checkout_version"])
FLAG_GAUGE = Gauge("feature_flag_enabled", "1 if a feature flag is enabled", ["flag"])
APP_INFO = Gauge("app_info", "Application info", ["version", "instance"])
APP_INFO.labels(APP_VERSION, INSTANCE).set(1)


# ---------------- feature flags ----------------
def load_flags():
    """Flags are re-read on every request, so they can be toggled without a redeploy.
    An environment variable FLAG_<NAME>=true/false overrides the file."""
    try:
        with open(FLAGS_FILE, encoding="utf-8") as f:
            flags = json.load(f)
    except (OSError, ValueError):
        flags = {}
    for key, value in os.environ.items():
        if key.startswith("FLAG_"):
            flags[key[5:].lower()] = value.lower() in ("1", "true", "on", "yes")
    return flags


def is_enabled(name, user="anonymous"):
    """A flag is either true/false or {"enabled": true, "rollout": 30} for a percentage rollout."""
    flag = load_flags().get(name, False)
    if isinstance(flag, dict):
        if not flag.get("enabled", False):
            return False
        bucket = int(hashlib.sha256(f"{name}:{user}".encode()).hexdigest(), 16) % 100
        return bucket < int(flag.get("rollout", 100))
    return bool(flag)


def create_app():
    app = Flask(__name__)

    @app.before_request
    def _start():
        g.t0 = time.perf_counter()
        g.user = request.args.get("user") or request.headers.get("X-User", "anonymous")

    @app.after_request
    def _record(resp):
        dur = time.perf_counter() - g.t0
        endpoint = request.url_rule.rule if request.url_rule else "unknown"
        if endpoint != "/metrics":
            REQUESTS.labels(request.method, endpoint, resp.status_code).inc()
            LATENCY.labels(endpoint).observe(dur)
            level = logging.ERROR if resp.status_code >= 500 else (
                logging.WARNING if resp.status_code >= 400 else logging.INFO)
            log.log(level, "%s %s %s %s %.1fms user=%s instance=%s",
                    request.headers.get("X-Forwarded-For", request.remote_addr), request.method,
                    request.path, resp.status_code, dur * 1000, g.user, INSTANCE)
        return resp

    @app.route("/")
    def index():
        return render_template("index.html", products=PRODUCTS, version=APP_VERSION, instance=INSTANCE,
                               dark=is_enabled("dark_mode", g.user),
                               recommend=is_enabled("recommendations", g.user))

    @app.route("/health")
    def health():
        return jsonify(status="ok", version=APP_VERSION, instance=INSTANCE)

    @app.route("/api/products")
    def products():
        time.sleep(random.uniform(0.005, 0.03))
        return jsonify(products=PRODUCTS, instance=INSTANCE)

    @app.route("/api/products/<int:pid>")
    def product(pid):
        for p in PRODUCTS:
            if p["id"] == pid:
                return jsonify(p)
        return jsonify(error="product not found"), 404

    @app.route("/checkout", methods=["GET", "POST"])
    def checkout():
        new = is_enabled("new_checkout", g.user)
        version = "v2" if new else "v1"
        time.sleep(random.uniform(0.01, 0.05) if new else random.uniform(0.05, 0.15))
        ORDERS.labels(version).inc()
        total = sum(p["price"] for p in PRODUCTS[:2])
        if new:
            return jsonify(checkout="v2", steps=1, message="One-click checkout", total=total, user=g.user)
        return jsonify(checkout="v1", steps=3, message="Classic 3-step checkout", total=total, user=g.user)

    @app.route("/flags")
    def flags():
        current = load_flags()
        for name, value in current.items():
            FLAG_GAUGE.labels(name).set(1 if (value.get("enabled") if isinstance(value, dict) else value) else 0)
        return jsonify(flags=current, evaluated_for=g.user,
                       result={n: is_enabled(n, g.user) for n in current})

    @app.route("/api/slow")
    def slow():
        time.sleep(random.uniform(0.3, 0.8))
        return jsonify(status="done", note="deliberately slow endpoint")

    @app.route("/api/error")
    def error():
        log.error("payment gateway timeout while processing order user=%s", g.user)
        return jsonify(error="internal error"), 500

    @app.route("/metrics")
    def metrics():
        for name, value in load_flags().items():
            FLAG_GAUGE.labels(name).set(1 if (value.get("enabled") if isinstance(value, dict) else value) else 0)
        return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

    return app


app = create_app()

if __name__ == "__main__":
    # dev server only; listens on localhost unless HOST is set (production uses gunicorn)
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "8000")))

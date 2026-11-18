import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))
import app as shop  # noqa: E402


@pytest.fixture
def client(tmp_path, monkeypatch):
    flags = tmp_path / "flags.json"
    flags.write_text(json.dumps({"new_checkout": False, "dark_mode": False,
                                 "recommendations": {"enabled": True, "rollout": 50}}))
    monkeypatch.setattr(shop, "FLAGS_FILE", str(flags))
    for k in list(os.environ):
        if k.startswith("FLAG_"):
            monkeypatch.delenv(k)
    c = shop.app.test_client()
    c.flags_path = flags
    return c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.get_json()["status"] == "ok"


def test_products(client):
    assert len(client.get("/api/products").get_json()["products"]) == 4


def test_product_not_found(client):
    assert client.get("/api/products/99").status_code == 404


def test_checkout_flag_off_uses_v1(client):
    assert client.post("/checkout").get_json()["checkout"] == "v1"


def test_flag_toggle_without_restart(client):
    client.flags_path.write_text(json.dumps({"new_checkout": True}))
    assert client.post("/checkout").get_json()["checkout"] == "v2"


def test_env_override(client, monkeypatch):
    monkeypatch.setenv("FLAG_NEW_CHECKOUT", "true")
    assert client.post("/checkout").get_json()["checkout"] == "v2"


def test_percentage_rollout_is_stable_and_partial(client):
    users = [f"user{i}" for i in range(200)]
    on = [u for u in users if shop.is_enabled("recommendations", u)]
    assert 60 < len(on) < 140                                   # roughly 50 %
    assert on == [u for u in users if shop.is_enabled("recommendations", u)]  # same user, same result


def test_metrics_exposed(client):
    client.get("/health")
    body = client.get("/metrics").get_data(as_text=True)
    assert "http_requests_total" in body and "feature_flag_enabled" in body

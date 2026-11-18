"""Load test for ShopLite. Run: locust -f tests/load/locustfile.py --headless -u 50 -r 10 -t 60s --host http://localhost:8000"""
import random

from locust import HttpUser, between, task


class Shopper(HttpUser):
    wait_time = between(0.2, 1.0)

    def on_start(self):
        self.user = f"load{random.randint(1, 500)}"

    @task(5)
    def browse_products(self):
        self.client.get(f"/api/products?user={self.user}", name="/api/products")

    @task(3)
    def home_page(self):
        self.client.get(f"/?user={self.user}", name="/")

    @task(2)
    def product_detail(self):
        self.client.get(f"/api/products/{random.randint(1, 4)}", name="/api/products/[id]")

    @task(2)
    def checkout(self):
        with self.client.post(f"/checkout?user={self.user}", name="/checkout", catch_response=True) as r:
            if r.json().get("checkout") not in ("v1", "v2"):
                r.failure("unexpected checkout response")

    @task(1)
    def health(self):
        self.client.get("/health")

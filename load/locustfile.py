"""Locust load profile (M4): browse-heavy mix + full buyer checkout.

Run: pip install locust
     docker compose exec api python scripts/seed_load.py   # 5000-unit product
     locust -f load/locustfile.py --headless -u 200 -r 20 --run-time 90s \
       --host http://localhost:8000 --csv load/results
Targets (Section 8): p95 <300ms catalog reads, <1.5s checkout, errors <1%.
"""
import uuid

from locust import HttpUser, between, task


class Browser(HttpUser):
    weight = 5
    wait_time = between(0.5, 2.0)

    @task(3)
    def list_products(self):
        self.client.get("/api/v1/products?page=1&page_size=20", name="catalog:list")

    @task(2)
    def search(self):
        self.client.get("/api/v1/products/search?q=mouse&page_size=10", name="catalog:search")

    @task(1)
    def detail_and_recs(self):
        self.client.get("/api/v1/products/1", name="catalog:detail")
        self.client.get("/api/v1/products/1/recommendations", name="catalog:recs")


class Buyer(HttpUser):
    weight = 1
    wait_time = between(1.0, 3.0)

    def on_start(self):
        email = f"load-{uuid.uuid4().hex[:8]}@example.com"
        self.client.post("/api/v1/auth/register",
                         json={"email": email, "password": "Password123!"})
        tok = self.client.post("/api/v1/auth/login",
                               json={"email": email, "password": "Password123!"}).json()
        self.h = {"Authorization": f"Bearer {tok['access_token']}"}

    @task
    def buy(self):
        pid = 999999  # replaced by seed_load.py product id lookup below
        prods = self.client.get("/api/v1/products/search?q=LOAD&page_size=5").json()
        if prods["items"]:
            pid = prods["items"][0]["id"]
        self.client.post("/api/v1/cart/items",
                         json={"product_id": pid, "quantity": 1}, headers=self.h,
                         name="cart:add")
        self.client.post("/api/v1/orders", json={"shipping_address": {"country": "US"}},
                         headers={**self.h, "Idempotency-Key": uuid.uuid4().hex},
                         name="orders:checkout")


class Support(HttpUser):
    weight = 1
    wait_time = between(2.0, 5.0)

    def on_start(self):
        tok = self.client.post("/api/v1/auth/login",
                               json={"email": "support@example.com",
                                     "password": "Password123!"}).json()
        self.h = {"Authorization": f"Bearer {tok['access_token']}"}

    @task(2)
    def list_orders(self):
        self.client.get("/api/v1/orders?page=1&page_size=20", headers=self.h,
                        name="support:orders")

    @task(1)
    def review_queue(self):
        self.client.get("/api/v1/orders/review/queue", headers=self.h, name="support:queue")

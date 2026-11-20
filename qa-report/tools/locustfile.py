"""بار همزمان روی API. توکن‌ها از /tmp/qa/tokens.txt (هر خط: token|member_id).
member_id=0 فقط برای ادمین است. مسیرهای مخصوص کارکنان فقط با ادمین فراخوانی می‌شوند."""
import random
from locust import HttpUser, task, between

ROWS = [l.strip().split("|") for l in open("/tmp/qa/tokens.txt") if l.strip()]
MEMBERS = [(t, int(m)) for t, m in ROWS if int(m) > 0]
ADMIN = [t for t, m in ROWS if int(m) == 0][0]


class Member(HttpUser):
    weight = 19
    wait_time = between(0.5, 1.5)

    def on_start(self):
        tok, mid = random.choice(MEMBERS)
        self.h = {"Authorization": f"Bearer {tok}"}
        self.mid = mid

    @task(3)
    def me(self):
        self.client.get("/api/v1/members/me", headers=self.h, name="/members/me")

    @task(2)
    def classes(self):
        self.client.get("/api/v1/classes", headers=self.h, name="/classes")

    @task(1)
    def wallet(self):
        self.client.get(f"/api/v1/payments/wallet/{self.mid}", headers=self.h, name="/payments/wallet/{id}")

    @task(1)
    def shop(self):
        self.client.get("/api/v1/shop/products", headers=self.h, name="/shop/products")


class Staff(HttpUser):
    weight = 1
    wait_time = between(0.5, 1.5)

    def on_start(self):
        self.h = {"Authorization": f"Bearer {ADMIN}"}

    @task(2)
    def programs(self):
        self.client.get("/api/v1/programs", headers=self.h, name="/programs")

    @task(1)
    def kpis(self):
        self.client.get("/api/v1/admin/kpis", headers=self.h, name="/admin/kpis")

    @task(1)
    def members(self):
        self.client.get("/api/v1/admin/members-summary", headers=self.h, name="/admin/members-summary")

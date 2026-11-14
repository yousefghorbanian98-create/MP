"""تست بار Locust — «کاربران فیک» باشگاه (M22-c5 / M30).

اجرا (از ریشهٔ پروژه، بعد از بالا آوردن بک‌اند):
    /tmp/tools-venv/bin/locust -f mp-app/backend/tests/load/locustfile.py \
        --headless -u 40 -r 8 -t 20s --host http://127.0.0.1:8000 \
        --csv=finn/reports/load/M22-smoke -q

قاعدهٔ E09: فقط دادهٔ ساختگی؛ هیچ کاربر واقعی در تست بار ساخته نمی‌شود.
"""

from locust import HttpUser, between, task


class GymVisitor(HttpUser):
    """بازدیدکنندهٔ عمومی: سلامت، manifest آپدیت، مستندات."""

    wait_time = between(0.3, 1.2)

    @task(3)
    def health(self) -> None:
        self.client.get("/health", name="/health")

    @task(4)
    def updates_manifest(self) -> None:
        self.client.get(
            "/api/v1/updates/manifest?platform=web&current=1.0.0", name="/updates/manifest"
        )

    @task(1)
    def openapi(self) -> None:
        self.client.get("/openapi.json", name="/openapi.json")


class GymAuthUser(HttpUser):
    """مسیر ورود/OTP — رفتار نزدیک به اوج ورود اعضا (با محدودیت نرخ)."""

    wait_time = between(0.5, 1.5)

    @task(2)
    def otp_request(self) -> None:
        # شماره‌های ساختگی — ۴۲۹ هم نتیجهٔ معتبر تست است (rate-limit باید دوام بیاورد)
        self.client.post(
            "/api/v1/auth/otp/request",
            json={"phone": "09120000000"},
            name="/auth/otp/request",
        )

    @task(1)
    def health(self) -> None:
        self.client.get("/health", name="/health")

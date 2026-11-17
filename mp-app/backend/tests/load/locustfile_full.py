"""تست بار جامع (M46-c4) — همهٔ مسیرهای پرترافیک با کاربران همزمان.

هدف: پاسخ به یک پرسش مشخص — «زیر بار، برنامه کرش می‌کند یا نه؟»

اجرا:
    TOKEN=... MP_HOST=http://127.0.0.1:8000 \
      /tmp/tools/venv/bin/locust -f tests/load/locustfile_full.py \
      --headless -u 50 -r 10 -t 60s --only-summary

سه پروفایل کاربر:
  StudioUser   — مربی/مدیر که داشبورد را باز می‌کند (خواندن سنگین)
  MemberUser   — عضو که برنامه و پروفایل خودش را می‌بیند
  KioskUser    — کیوسک چک‌این (نوشتن سبک، پرتکرار)

هر ریسک واقعی را fail می‌کنیم: ۵xx = شکست تست، نه فقط لاگ.
"""

from __future__ import annotations

import os
import random
from datetime import UTC, datetime

from locust import HttpUser, between, task

TOKEN = os.environ.get("TOKEN", "")
AUTH = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


class BaseUser(HttpUser):
    abstract = True

    def _get(self, path: str, name: str | None = None) -> None:
        with self.client.get(path, headers=AUTH, catch_response=True, name=name or path) as r:
            if r.status_code >= 500:
                r.failure(f"server error {r.status_code}")
            elif r.status_code == 429:
                # محدودیت نرخ در ساعت اوج رفتار درست است؛ شکست نیست
                r.success()

    def _post(self, path: str, payload: dict | None = None, name: str | None = None) -> None:
        with self.client.post(
            path, json=payload, headers=AUTH, catch_response=True, name=name or path
        ) as r:
            if r.status_code >= 500:
                r.failure(f"server error {r.status_code}")
            elif r.status_code == 429:
                r.success()


class StudioUser(BaseUser):  # type: ignore[misc]
    """مربی/مدیر — خواندن سنگین داشبورد و فهرست‌ها."""

    weight = 3
    wait_time = between(0.3, 1.2)

    @task(4)
    def dashboard(self) -> None:
        self._get("/api/v1/admin/kpis")
        self._get("/api/v1/admin/attendance?days=30")

    @task(3)
    def members(self) -> None:
        self._get("/api/v1/admin/members-summary")
        self._get("/api/v1/admin/checkins?limit=50")

    @task(2)
    def programs(self) -> None:
        self._get("/api/v1/programs?limit=50")
        self._get("/api/v1/programs?status=pending")

    @task(2)
    def finance(self) -> None:
        self._get("/api/v1/payments/finance/summary")

    @task(1)
    def flags(self) -> None:
        self._get("/api/v1/admin/flags")

    @task(1)
    def analytics(self) -> None:
        self._get("/api/v1/admin/analytics/leaderboards")
        self._get("/api/v1/admin/analytics/churn-risk")


class MemberUser(BaseUser):  # type: ignore[misc]
    """عضو — پروفایل و برنامهٔ خودش."""

    weight = 5
    wait_time = between(0.5, 2.0)

    @task(3)
    def me(self) -> None:
        self._get("/api/v1/members/me")

    @task(2)
    def my_programs(self) -> None:
        self._get("/api/v1/programs/member/1", name="/api/v1/programs/member/[id]")

    @task(2)
    def volume_report(self) -> None:
        """G2 — سنگین‌ترین مسیر خواندن: چند join + محاسبهٔ نشانگرها."""
        self._get(
            "/api/v1/programs/member/1/volume",
            name="/api/v1/programs/member/[id]/volume",
        )

    @task(2)
    def my_assessments(self) -> None:
        self._get("/api/v1/axis-assessments/member/1", name="/api/v1/axis-assessments/member/[id]")

    @task(1)
    def wallet(self) -> None:
        self._get("/api/v1/payments/wallet/1", name="/api/v1/payments/wallet/[id]")

    @task(2)
    def exercise_library(self) -> None:
        """G9 — کتابخانهٔ حرکات: پنجرهٔ تصویر + فیلتر (خواندن + فایل استاتیک)."""
        self._get("/api/v1/library/exercises?muscle_group=legs")
        self._get("/api/v1/library/exercises/1", name="/api/v1/library/exercises/[id]")
        self._get("/static/exercises/1_0.jpg", name="/static/exercises/[img]")

    @task(2)
    def readiness(self) -> None:
        """G13 — آمادگی: چند aggregate روی بازخورد ست‌ها."""
        self._get(
            "/api/v1/programs/member/1/readiness", name="/api/v1/programs/member/[id]/readiness"
        )

    @task(1)
    def offline_sync(self) -> None:
        """G7 — سنک آفلاین: نوشتن با کلید idempotent؛ تکرار بی‌اثر است."""
        cid = f"load-{random.randint(1, 10**9)}"
        payload = {
            "member_id": 1,
            "items": [
                {
                    "client_id": cid,
                    "device_id": "load-test",
                    "updated_at": datetime.now(UTC).isoformat(),
                    "movement_id": "back_squat",
                    "weight": 60.0,
                    "target_reps": 10,
                    "reps_done": 9,
                    "rir": 2.0,
                    "soreness": 3,
                    "program_id": 1,
                }
            ],
        }
        self._post("/api/v1/programs/sync/set-feedback", payload)

    @task(1)
    def health(self) -> None:
        self._get("/health")


class KioskUser(BaseUser):  # type: ignore[misc]
    """کیوسک پذیرش — چک‌این پرتکرار (نوشتن سبک)."""

    weight = 2
    wait_time = between(1.0, 3.0)

    @task(3)
    def exit_checkin(self) -> None:
        # چک‌این ناموجود ⇒ ۴۰۴ پاسخ *درست* است (نه شکست). فقط ۵xx شکست است.
        with self.client.post(
            f"/api/v1/face/checkins/{random.randint(900000, 999999)}/exit",
            headers=AUTH,
            catch_response=True,
            name="/api/v1/face/checkins/[id]/exit",
        ) as r:
            if r.status_code >= 500:
                r.failure(f"server error {r.status_code}")
            elif r.status_code in (403, 404, 429):
                r.success()

    @task(2)
    def qr_token(self) -> None:
        self._get("/api/v1/face/qr-token")

    @task(1)
    def privacy(self) -> None:
        self._get("/api/v1/face/privacy-notice")


class AnonUser(BaseUser):  # type: ignore[misc]
    """کاربر بدون توکن — OTP و محدودیت نرخ."""

    weight = 1
    wait_time = between(1.0, 2.0)

    @task(2)
    def health(self) -> None:
        with self.client.get("/health", catch_response=True) as r:
            if r.status_code >= 500:
                r.failure(f"server error {r.status_code}")

    @task(1)
    def otp_request(self) -> None:
        phone = f"09{random.randint(100000000, 999999999)}"
        with self.client.post(
            "/api/v1/auth/otp/request", json={"phone": phone}, catch_response=True
        ) as r:
            if r.status_code >= 500:
                r.failure(f"server error {r.status_code}")
            elif r.status_code == 429:
                r.success()

"""تست‌های رزرو کلاس (ظرفیت/لیست انتظار/ارتقا) + مالی/کمیسیون (M27)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine

from ._actors import create_actor

_counter = itertools.count(500001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/cls.db")
    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


@pytest.fixture()
def auth():
    """هدر کاربر تازه؛ `grants` مجوزهای شخصی فاز ۵ را هم می‌سازد."""

    def _auth(role: str = "manager", grants: list[str] | None = None) -> dict:
        return create_actor(role, grants)

    return _auth


def _member(client, h, phone):
    return client.post(
        "/api/v1/members",
        json={"phone": phone, "full_name": "عضو کلاس", "gender": "male"},
        headers=h,
    ).json()


def test_booking_capacity_waitlist_promotion(client, auth):
    h = auth("manager", grants=["finance.write"])
    cls = client.post("/api/v1/classes", json={"name": "یوگا", "capacity": 2}, headers=h).json()
    members = [_member(client, h, f"0912000{i:04d}") for i in range(3)]
    b1 = client.post(
        "/api/v1/classes/book",
        json={"class_id": cls["id"], "member_id": members[0]["id"]},
        headers=h,
    ).json()
    b2 = client.post(
        "/api/v1/classes/book",
        json={"class_id": cls["id"], "member_id": members[1]["id"]},
        headers=h,
    ).json()
    b3 = client.post(
        "/api/v1/classes/book",
        json={"class_id": cls["id"], "member_id": members[2]["id"]},
        headers=h,
    ).json()
    assert b1["status"] == "confirmed" and b2["status"] == "confirmed"
    assert b3["status"] == "waitlisted"  # ظرفیت پر
    # لغو نفر اول ← ارتقای لیست انتظار
    client.post(
        "/api/v1/classes/cancel",
        json={"class_id": cls["id"], "member_id": members[0]["id"]},
        headers=h,
    )
    listing = client.get("/api/v1/classes", headers=h).json()[0]
    assert listing["confirmed"] == 2 and listing["waitlisted"] == 0
    # رزرو تکراری ممنوع
    dup = client.post(
        "/api/v1/classes/book",
        json={"class_id": cls["id"], "member_id": members[1]["id"]},
        headers=h,
    )
    assert dup.status_code == 400


def test_finance_summary_csv_commission(client, auth):
    h = auth("manager", grants=["finance.write"])
    m = _member(client, h, "09129990001")
    auth("coach")  # ایجاد کاربر مربی برای انتساب کمیسیون
    # پرداخت با انتساب مربی
    pay = client.post(
        "/api/v1/payments",
        json={
            "member_id": m["id"],
            "amount_rial": 1000000,
            "method": "cash",
            "description": "اشتراک",
        },
        headers=h,
    ).json()
    client.post(f"/api/v1/payments/{pay['id']}/verify", json={}, headers=h)
    summary = client.get("/api/v1/payments/finance/summary", headers=h).json()
    assert summary["total_paid_rial"] == 1000000
    csv_text = client.get("/api/v1/payments/finance/export.csv", headers=h).text
    assert "amount_rial" in csv_text and "1000000" in csv_text
    # کمیسیون (بدون انتساب ← صفر)
    coach_user_id = None
    from db.models import Payment, User

    with get_session_factory()() as s:
        u = s.query(User).filter(User.role == "coach").first()
        coach_user_id = u.id
        p = s.get(Payment, pay["id"])
        p.coach_id = coach_user_id
        s.commit()
    comm = client.post(
        "/api/v1/payments/finance/commission",
        json={"coach_id": coach_user_id, "rate": 0.1},
        headers=h,
    ).json()
    assert comm["commission_rial"] == 100000  # ۱۰٪

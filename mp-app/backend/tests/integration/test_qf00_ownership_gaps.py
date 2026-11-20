"""QF-00 — دو شکاف مالکیت که inventory سطح-route پیدا کرد (red → green).

# یافته‌ها

1. `POST /api/v1/payments/{payment_id}/start` برای نقش `member` در policy
   کاسبن باز است و کامنت policy می‌گوید «کنترل کدام تراکنش در service است»،
   اما handler نه کاربر را می‌گرفت و نه service مالکیت را می‌سنجید. هر عضو
   می‌توانست با شناسهٔ تراکنشِ عضو دیگر، نشست درگاه بسازد؛ و چون
   `already_started` جلوی شروع دوباره را می‌گیرد، صاحب واقعی دیگر
   نمی‌توانست پرداخت خودش را آغاز کند.
2. `GET /api/v1/members/memberships/{membership_id}/invoice` برای `member`
   باز است (policy `/members/*` GET) ولی handler پارامتر `user` را نادیده
   می‌گرفت؛ خروجی شامل `member_id`، `price_rial`، `gender` و بازهٔ اشتراک
   عضو دیگر بود.

این تست‌ها فقط همان دو مسیر را می‌بندند؛ inventory کامل و QA مستقل QF-00
جدا هستند و این فایل اثبات گردش کامل مالی نیست.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(982001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/scope.db")
    monkeypatch.setattr(settings, "payment_gateway", "mock")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


def _user(role: str) -> tuple[dict[str, str], int]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}{n}", role=role)
        s.add(u)
        s.commit()
        uid = u.id
    return {"Authorization": f"Bearer {create_access_token(uid, role)}"}, uid


def _member() -> tuple[dict[str, str], int]:
    from db.base import get_session_factory
    from db.models import Member

    headers, uid = _user("member")
    with get_session_factory()() as s:
        m = Member(user_id=uid, gender="male", goal="x", branch_id=1)
        s.add(m)
        s.commit()
        return headers, m.id


def _payment(client, headers, member_id: int) -> dict:
    r = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 150_000, "method": "card_to_card"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()


def _membership(member_id: int) -> int:
    from datetime import UTC, datetime, timedelta

    from db.base import get_session_factory
    from db.models import Membership

    with get_session_factory()() as s:
        ms = Membership(
            member_id=member_id,
            plan_name="ماهانه",
            started_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=30),
            price_rial=900_000,
            status="active",
        )
        s.add(ms)
        s.commit()
        return ms.id


def test_member_cannot_start_another_members_payment(client) -> None:
    owner_h, owner_mid = _member()
    attacker_h, _ = _member()
    payment = _payment(client, owner_h, owner_mid)

    r = client.post(
        f"/api/v1/payments/{payment['id']}/start",
        json={},
        headers=attacker_h,
    )
    assert r.status_code == 403, r.text


def test_member_can_still_start_own_payment(client) -> None:
    owner_h, owner_mid = _member()
    payment = _payment(client, owner_h, owner_mid)

    r = client.post(f"/api/v1/payments/{payment['id']}/start", json={}, headers=owner_h)
    assert r.status_code == 200, r.text
    assert r.json()["authority"].startswith("MOCK-")


def test_reception_can_still_start_any_payment(client) -> None:
    owner_h, owner_mid = _member()
    staff_h, _ = _user("reception")
    payment = _payment(client, owner_h, owner_mid)

    r = client.post(f"/api/v1/payments/{payment['id']}/start", json={}, headers=staff_h)
    assert r.status_code == 200, r.text


def test_member_cannot_read_another_members_invoice(client) -> None:
    owner_h, owner_mid = _member()
    attacker_h, _ = _member()
    membership_id = _membership(owner_mid)

    r = client.get(
        f"/api/v1/members/memberships/{membership_id}/invoice",
        headers=attacker_h,
    )
    assert r.status_code == 403, r.text


def test_member_can_read_own_invoice_and_staff_reads_all(client) -> None:
    owner_h, owner_mid = _member()
    membership_id = _membership(owner_mid)

    own = client.get(f"/api/v1/members/memberships/{membership_id}/invoice", headers=owner_h)
    assert own.status_code == 200, own.text
    assert own.json()["membership_id"] == membership_id

    staff_h, _ = _user("reception")
    staff = client.get(f"/api/v1/members/memberships/{membership_id}/invoice", headers=staff_h)
    assert staff.status_code == 200, staff.text

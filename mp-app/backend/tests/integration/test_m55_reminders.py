"""G11 — یادآوری‌های پویا از دادهٔ واقعی DB.

مهم‌ترین چیز: **idempotency**. بدون آن، هر بازخوانی صفحه یک اعلان تکراری
می‌سازد و کاربر در سیل اعلان‌ها غرق می‌شود.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(997001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/rem.db")
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


def _staff() -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"c{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _member() -> int:
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"m{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, gender="male", goal="x", branch_id=1)
        s.add(m)
        s.commit()
        return m.id


def _membership(mid: int, days: int) -> None:
    from db.base import get_session_factory
    from db.models import Membership

    now = datetime.now(UTC)
    with get_session_factory()() as s:
        s.add(
            Membership(
                member_id=mid,
                plan_name="ماهانه",
                started_at=now - timedelta(days=30),
                expires_at=now + timedelta(days=days),
                status="active",
                price_rial=3_000_000,
            )
        )
        s.commit()


def _pending_payment(mid: int, amount: int) -> None:
    from db.base import get_session_factory
    from db.models import Payment

    with get_session_factory()() as s:
        s.add(Payment(member_id=mid, amount_rial=amount, status="pending", method="cash"))
        s.commit()


def test_member_with_no_data_gets_explicit_skips(client: TestClient) -> None:
    h = _staff()
    mid = _member()

    body = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    assert body["reminders"] == []
    assert len(body["skipped"]) == 3
    assert body["data_sources"]["membership"] is False


def test_expiring_membership_creates_a_reminder(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    _membership(mid, days=3)

    body = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    keys = [r["key"] for r in body["reminders"]]
    assert "renewal" in keys
    assert body["created_notifications"] == 1


def test_second_call_is_idempotent(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    _membership(mid, days=3)

    first = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    assert first["created_notifications"] == 1

    second = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    assert second["created_notifications"] == 0, "یادآوری تکراری نباید ساخته شود"
    # خود یادآوری هنوز لازم است — فقط اعلان تکراری ساخته نمی‌شود
    assert len(second["reminders"]) == 1


def test_notification_is_actually_readable_by_the_member(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    _membership(mid, days=2)
    client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h)

    notes = client.get(f"/api/v1/notifications/member/{mid}", headers=h).json()
    assert len(notes) == 1
    assert notes[0]["kind"] == "renewal"
    assert "تمدید" in notes[0]["title"]


def test_pending_payment_is_surfaced(client: TestClient) -> None:
    h = _staff()
    mid = _member()
    _pending_payment(mid, 750_000)

    body = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    keys = [r["key"] for r in body["reminders"]]
    assert "payment_due" in keys
    assert body["data_sources"]["pending_payment"] is True


def test_paid_payment_is_not_surfaced(client: TestClient) -> None:
    from db.base import get_session_factory
    from db.models import Payment

    h = _staff()
    mid = _member()
    with get_session_factory()() as s:
        s.add(Payment(member_id=mid, amount_rial=500_000, status="paid", method="cash"))
        s.commit()

    body = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    assert "payment_due" not in [r["key"] for r in body["reminders"]]


def test_old_workout_feedback_triggers_inactivity(client: TestClient) -> None:
    from db.base import get_session_factory
    from db.models import SetFeedback

    h = _staff()
    mid = _member()
    with get_session_factory()() as s:
        s.add(
            SetFeedback(
                member_id=mid,
                movement_id="squat",
                weight=60.0,
                reps_done=10,
                target_reps=10,
                rir=2,
                soreness=3,
                created_at=datetime.now(UTC) - timedelta(days=20),
            )
        )
        s.commit()

    body = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    assert "inactivity" in [r["key"] for r in body["reminders"]]


def test_member_cannot_read_another_members_reminders(client: TestClient) -> None:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    _staff()  # نقش مربی برای این تست لازم نیست، فقط عضو مهاجم سنجیده می‌شود
    victim = _member()

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name="intruder", role="member")
        s.add(u)
        s.commit()
        s.add(Member(user_id=u.id, gender="male", goal="x", branch_id=1))
        s.commit()
        ih = {"Authorization": f"Bearer {create_access_token(u.id, 'member')}"}

    r = client.get(f"/api/v1/notifications/reminders/member/{victim}", headers=ih)
    assert r.status_code == 403


def test_unknown_member_is_404(client: TestClient) -> None:
    h = _staff()
    assert client.get("/api/v1/notifications/reminders/member/999999", headers=h).status_code == 404

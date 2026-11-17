"""گیت M45 — آزمون‌های endpoint حضور و خلاصهٔ اعضا (دادهٔ واقعی، نه mock).

قاعده‌ها:
- «داده ناشناخته است نه صفر» (E05): عضو بدون اشتراک `unknown` است، نه `expired`.
- بازهٔ زمانی صریح؛ پیش‌فرض ۳۰ روز، سقف ۳۶۵.
- هر پاسخ `rule_version` دارد (S3b: هر عدد باید روش داشته باشد).
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(950001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/attendance.db")
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


def _headers(role: str) -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _seed_member_and_checkins(*, count: int, closed: int, days_ago: int = 1) -> tuple[int, int]:
    """یک عضو واقعی + check-in ها می‌سازد. (member_id, user_id) برمی‌گرداند."""
    from db.base import get_session_factory
    from db.models import CheckIn, Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"member-{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, goal="hypertrophy", constraints="[]", gender="male")
        s.add(m)
        s.commit()
        base = datetime.now(UTC) - timedelta(days=days_ago)
        for i in range(count):
            started = base - timedelta(hours=i)
            s.add(
                CheckIn(
                    member_id=m.id,
                    method="qr",
                    result="ok",
                    created_at=started,
                    checked_out_at=started + timedelta(minutes=45) if i < closed else None,
                )
            )
        s.commit()
        return m.id, u.id


# ── حضور ──


def test_attendance_requires_auth(client: TestClient) -> None:
    """بدون توکن → رد (گارد قبل از هر خواندن cache — R-005)."""
    res = client.get("/api/v1/admin/attendance")
    assert res.status_code in (401, 403)


def test_attendance_rejects_member(client: TestClient) -> None:
    """عضو نباید حضور همهٔ باشگاه را ببیند."""
    res = client.get("/api/v1/admin/attendance", headers=_headers("member"))
    assert res.status_code == 403


def test_attendance_empty_db_returns_real_zero(client: TestClient) -> None:
    """DB خالی → صفر واقعی + rule_version، نه دادهٔ ساختگی."""
    res = client.get("/api/v1/admin/attendance?days=7", headers=_headers("coach"))
    assert res.status_code == 200
    body = res.json()
    assert body["total_checkins"] == 0
    assert body["closed_sessions"] == 0
    assert body["open_sessions"] == 0
    assert body["series"] == []
    assert body["rule_version"]


def test_attendance_counts_only_ok_and_separates_open_sessions(client: TestClient) -> None:
    """فقط check-in های ok شمرده می‌شوند؛ جلسهٔ باز دقیقه ندارد (نامعلوم ≠ صفر)."""
    from db.base import get_session_factory
    from db.models import CheckIn

    member_id, _ = _seed_member_and_checkins(count=3, closed=2)
    with get_session_factory()() as s:
        s.add(
            CheckIn(
                member_id=member_id,
                method="manual",
                result="denied",
                created_at=datetime.now(UTC),
            )
        )
        s.commit()

    res = client.get("/api/v1/admin/attendance?days=7", headers=_headers("coach"))
    assert res.status_code == 200
    body = res.json()
    assert body["total_checkins"] == 3, "check-in رد‌شده نباید شمرده شود"
    assert body["closed_sessions"] == 2
    assert body["open_sessions"] == 1
    assert body["total_minutes"] == 90, "دو جلسهٔ ۴۵ دقیقه‌ای"
    assert body["distinct_members"] == 1


def test_attendance_series_is_daily_and_counts_match(client: TestClient) -> None:
    """سری روزانه باید با مجموع سازگار باشد (جمع سری = total_checkins)."""
    _seed_member_and_checkins(count=4, closed=1, days_ago=2)
    res = client.get("/api/v1/admin/attendance?days=7", headers=_headers("manager"))
    body = res.json()
    assert sum(row["count"] for row in body["series"]) == body["total_checkins"]


def test_attendance_days_bounds(client: TestClient) -> None:
    """بازهٔ نامعتبر رد می‌شود (نه سکوت)."""
    h = _headers("coach")
    assert client.get("/api/v1/admin/attendance?days=0", headers=h).status_code == 422
    assert client.get("/api/v1/admin/attendance?days=400", headers=h).status_code == 422


# ── خلاصهٔ اعضا (اعضا/مالی استودیو) ──


def test_members_summary_rejects_member(client: TestClient) -> None:
    res = client.get("/api/v1/admin/members-summary", headers=_headers("member"))
    assert res.status_code == 403


def test_members_summary_unknown_is_not_expired(client: TestClient) -> None:
    """عضو بدون هیچ اشتراک status=unknown می‌گیرد، نه expired (E05)."""
    _seed_member_and_checkins(count=1, closed=0)
    res = client.get("/api/v1/admin/members-summary", headers=_headers("manager"))
    assert res.status_code == 200
    body = res.json()
    assert body["rule_version"]
    assert len(body["items"]) >= 1
    for item in body["items"]:
        assert item["status"] in {"active", "expiring", "expired", "unknown"}
        if item.get("membership_id") is None:
            assert item["status"] == "unknown", "بی‌اشتراک = نامعلوم، نه منقضی"
        else:
            assert item["status"] != "unknown"


def test_members_summary_expiring_window(client: TestClient) -> None:
    """اشتراکی که تا ۷ روز آینده تمام می‌شود = expiring؛ فعالِ دورتر = active."""
    from db.base import get_session_factory
    from db.models import Membership

    member_id, user_id = _seed_member_and_checkins(count=0, closed=0)
    now = datetime.now(UTC)
    with get_session_factory()() as s:
        s.add(
            Membership(
                member_id=member_id,
                plan_name="ماهانه",
                started_at=now - timedelta(days=23),
                expires_at=now + timedelta(days=3),
                status="active",
                price_rial=5_000_000,
            )
        )
        s.commit()

    body = client.get("/api/v1/admin/members-summary", headers=_headers("manager")).json()
    row = next(i for i in body["items"] if i["member_id"] == member_id)
    assert row["status"] == "expiring"
    assert row["days_left"] == 3
    assert row["full_name"]


def test_members_summary_returns_the_real_name_and_phone(client: TestClient) -> None:
    """رگرسیون باگ جابه‌جایی ستون‌ها.

    کوئری با `select(User.id, User.full_name, User.phone, ...)` اجرا می‌شد
    ولی مقادیر با ایندکس عددی خوانده می‌شدند: `full_name` در واقع id بود
    و `phone` در واقع نام کاربر. در استودیو یعنی جدول اعضا نام کاربر را
    به‌شکل `۱` و تلفن را به‌شکل `مربی مهدی` نشان می‌داد.

    تست قبلی فقط `assert row["full_name"]` داشت و id=1 هم truthy است،
    پس باگ زنده ماند. تست قرارداد زنده آن را گرفت و این‌جا تثبیت می‌شود.
    """
    member_id, user_id = _seed_member_and_checkins(count=0, closed=0)
    from db.base import get_session_factory
    from db.models import User

    with get_session_factory()() as s:
        u = s.get(User, user_id)
        u.full_name = "زهرا احمدی"
        u.phone = "09121112233"
        s.commit()

    body = client.get("/api/v1/admin/members-summary", headers=_headers("manager")).json()
    row = next(i for i in body["items"] if i["member_id"] == member_id)
    assert row["full_name"] == "زهرا احمدی"
    assert row["phone"] == "09121112233"
    assert row["user_id"] == user_id
    assert isinstance(row["full_name"], str)
    assert isinstance(row["is_active"], bool)


def test_members_summary_never_leaks_the_id_as_a_name(client: TestClient) -> None:
    """هیچ ردیفی نباید نامِ عددی داشته باشد."""
    _seed_member_and_checkins(count=1, closed=1)
    body = client.get("/api/v1/admin/members-summary", headers=_headers("manager")).json()
    for row in body["items"]:
        assert not isinstance(row["full_name"], int), f"نام عددی برای عضو {row['member_id']}"
        assert row["phone"] == "" or not isinstance(row["phone"], int)

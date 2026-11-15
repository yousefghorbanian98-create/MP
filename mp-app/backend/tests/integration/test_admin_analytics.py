"""تست‌های تحلیل‌های مدیریتی (M42-c1) — لیدربوردها از دادهٔ واقعی + نامعلوم ≠ صفر."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(930001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/analytics.db")
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


def _seed_member(name: str) -> int:
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=name, role="member")
        s.add(u)
        s.flush()
        m = Member(user_id=u.id, gender="male")
        s.add(m)
        s.commit()
        return m.id


def test_leaderboards_from_real_data(client) -> None:
    """M42-c1 — سه لیدربورد از دادهٔ واقعی + روش محاسبهٔ هر رتبه."""
    from db.base import get_session_factory
    from db.models import AxisAssessment, AxisScore, CheckIn, Payment

    a1 = _seed_member("ورزشکار قوی")
    a2 = _seed_member("ورزشکار متوسط")
    s1 = _seed_member("پرداخت‌کنندهٔ اصلی")
    v1 = _seed_member("منظم‌ترین")

    now = datetime.now(UTC)
    with get_session_factory()() as s:
        # ارزیابی‌ها: a1 بالاتر از a2 (a2 یک محور missing دارد و در میانگین نمی‌آید)
        aa1 = AxisAssessment(member_id=a1, status="draft")
        aa2 = AxisAssessment(member_id=a2, status="draft")
        s.add_all([aa1, aa2])
        s.flush()
        s.add_all(
            [
                AxisScore(assessment_id=aa1.id, axis=1, score=90.0, quality="high"),
                AxisScore(assessment_id=aa1.id, axis=2, score=80.0, quality="high"),
                AxisScore(assessment_id=aa2.id, axis=1, score=60.0, quality="medium"),
                AxisScore(assessment_id=aa2.id, axis=2, score=None, quality="missing"),
            ]
        )
        # پرداخت‌ها: s1 بیشترین جمع paid؛ یک pending نباید بشمارد
        s.add_all(
            [
                Payment(member_id=s1, amount_rial=5_000_000, status="paid", paid_at=now),
                Payment(member_id=s1, amount_rial=3_000_000, status="paid", paid_at=now),
                Payment(member_id=s1, amount_rial=9_000_000, status="pending", paid_at=None),
                Payment(member_id=a1, amount_rial=2_000_000, status="paid", paid_at=now),
            ]
        )
        # چک‌این‌ها: v1 بیشترین مراجعه
        for i in range(6):
            s.add(
                CheckIn(member_id=v1, method="qr", result="ok", created_at=now - timedelta(days=i))
            )
        s.add(CheckIn(member_id=v1, method="qr", result="denied", created_at=now))
        s.add(CheckIn(member_id=a1, method="face", result="ok", created_at=now))
        s.commit()

    h = _headers("manager")
    res = client.get("/api/v1/admin/analytics/leaderboards", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()

    athletes = body["top_athletes"]
    assert athletes[0]["member_id"] == a1
    assert athletes[0]["avg_axis_score"] == 85.0
    # a2: فقط محور ۱ (۶۰) — محور missing در میانگین نیامده
    assert athletes[1]["avg_axis_score"] == 60.0
    assert athletes[1]["axes_counted"] == 1
    assert all(a["method"] for a in athletes)

    spenders = body["top_spenders"]
    assert spenders[0]["member_id"] == s1
    assert spenders[0]["total_paid_rial"] == 8_000_000  # pending نیامده
    assert spenders[0]["payments_count"] == 2

    visits = body["most_visits"]
    assert visits[0]["member_id"] == v1
    assert visits[0]["visits"] == 6  # denied نیامده
    assert visits[0]["distinct_days"] == 6
    assert body["rule_version"]


def test_leaderboards_rbac_and_empty_state(client) -> None:
    """M42-c1 — فقط مدیریت؛ حالت خالی = آرایهٔ خالی (نه صفرهای دروغین)."""
    h_member = _headers("member")
    res = client.get("/api/v1/admin/analytics/leaderboards", headers=h_member)
    assert res.status_code == 403

    h = _headers("super_admin")
    res = client.get("/api/v1/admin/analytics/leaderboards", headers=h)
    assert res.status_code == 200
    body = res.json()
    assert body["top_athletes"] == []
    assert body["top_spenders"] == []
    assert body["most_visits"] == []


def test_most_time_and_checkout_flow(client) -> None:
    """M42-c2 — ثبت خروج ← رتبهٔ بیشترین تایم؛ جلسهٔ باز دقیقه ندارد."""
    from db.base import get_session_factory
    from db.models import CheckIn

    m1 = _seed_member("پر-حضور")
    m2 = _seed_member("کم‌حضور")
    now = datetime.now(UTC)
    with get_session_factory()() as s:
        c1 = CheckIn(
            member_id=m1,
            method="qr",
            result="ok",
            created_at=now - timedelta(hours=3),
            checked_out_at=now - timedelta(hours=1),
        )
        c2 = CheckIn(
            member_id=m1,
            method="qr",
            result="ok",
            created_at=now - timedelta(days=1, hours=2),
            checked_out_at=now - timedelta(days=1),
        )
        c3 = CheckIn(member_id=m1, method="qr", result="ok", created_at=now)  # باز — بدون دقیقه
        c4 = CheckIn(
            member_id=m2,
            method="qr",
            result="ok",
            created_at=now - timedelta(hours=2),
            checked_out_at=now - timedelta(hours=1),
        )
        s.add_all([c1, c2, c3, c4])
        s.commit()
        open_id = c3.id

    h = _headers("manager")
    res = client.get("/api/v1/admin/analytics/leaderboards", headers=h)
    assert res.status_code == 200
    most = res.json()["most_time"]
    assert most[0]["member_id"] == m1
    assert most[0]["total_minutes"] == 240  # ۱۲۰ + ۱۲۰
    assert most[0]["closed_sessions"] == 2
    assert most[0]["open_sessions"] == 1  # جلسهٔ باز — فقط شمارش، نه دقیقه
    assert most[1]["member_id"] == m2
    assert most[1]["total_minutes"] == 60

    # ثبت خروج جلسهٔ باز ← دقیقه‌ها به‌روز می‌شوند؛ خروج دوباره = خطا
    res = client.post(f"/api/v1/face/checkins/{open_id}/exit", headers=h)
    assert res.status_code == 200, res.text
    res = client.post(f"/api/v1/face/checkins/{open_id}/exit", headers=h)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "already_checked_out"

    res = client.get("/api/v1/admin/analytics/leaderboards", headers=h)
    most = res.json()["most_time"]
    assert most[0]["open_sessions"] == 0
    assert most[0]["closed_sessions"] == 3


def test_churn_risk_endpoint_with_real_facts(client) -> None:
    """M44-c2 — ریسک ریزش از دادهٔ واقعی؛ بدون داده = unknown نه صفر."""
    from db.base import get_session_factory
    from db.models import CheckIn, Membership

    risky = _seed_member("در خطر ریزش")
    loyal = _seed_member("وفادار")
    ghost = _seed_member("بدون داده")
    now = datetime.now(UTC)
    with get_session_factory()() as s:
        s.add(
            CheckIn(member_id=risky, method="qr", result="ok", created_at=now - timedelta(days=35))
        )
        s.add(
            Membership(
                member_id=risky,
                plan_name="m",
                started_at=now - timedelta(days=70),
                expires_at=now - timedelta(days=5),
                status="active",
                price_rial=1,
            )
        )
        for i in range(9):
            s.add(
                CheckIn(
                    member_id=loyal, method="qr", result="ok", created_at=now - timedelta(days=i)
                )
            )
        s.commit()

    h = _headers("manager")
    res = client.get("/api/v1/admin/analytics/churn-risk", headers=h)
    assert res.status_code == 200, res.text
    body = res.json()
    rows = {row["member_id"]: row for row in body["risk_rows"]}

    assert rows[risky]["band"] == "high"
    assert rows[risky]["signals"]
    assert rows[loyal]["band"] == "low"
    assert rows[ghost]["band"] == "unknown"  # نامعلوم ≠ صفر
    assert rows[ghost]["risk_score"] is None
    # ترتیب: high اول
    assert body["risk_rows"][0]["member_id"] == risky

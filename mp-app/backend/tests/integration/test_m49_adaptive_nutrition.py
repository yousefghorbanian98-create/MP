"""G3 — تغذیهٔ سازگار، از رکوردهای واقعی DB تا پیشنهاد کالری (M49-c3)."""

from __future__ import annotations

import itertools
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(973001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/adaptive.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        _seed_food()
        yield c
    reset_engine()


FOOD_ID_HOLDER: dict[str, int] = {}


def _seed_food() -> None:
    """یک غذای «۱۰۰ کالری در ۱۰۰ گرم» تا محاسبه در تست قابل پیش‌بینی باشد."""
    from db.base import get_session_factory
    from db.models import FoodItem

    with get_session_factory()() as s:
        f = FoodItem(
            external_id="test:meal-100kcal",
            name_fa="وعدهٔ آزمایشی ۱۰۰ کالری",
            kcal_per_100g=100,
            protein_g_per_100g=10.0,
            carbs_g_per_100g=10.0,
            fat_g_per_100g=1.1,
            category="آزمایشی",
        )
        s.add(f)
        s.commit()
        FOOD_ID_HOLDER["id"] = f.id


def _staff() -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"coach-{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _member(client: TestClient, h: dict, goal: str = "weight_loss") -> int:
    n = next(_counter)
    r = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"عضو {n}", "gender": "male"},
        headers=h,
    )
    assert r.status_code in (200, 201), r.text
    mid = r.json()["id"]
    # هدف عضو برای ضریب اصلاح لازم است
    from db.base import get_session_factory
    from db.models import Member

    with get_session_factory()() as s:
        m = s.get(Member, mid)
        m.goal = goal
        s.commit()
    return mid


def _scenario(client: TestClient, h: dict, mid: int, *, days: int = 28) -> None:
    """سناریوی کنترل‌شده: شروع ۸۰ کیلو، کاهش ۰٫۵ کیلو/هفته، مصرف ۲۱۰۰ کالری.

    ⇒ TDEE واقعی ≈ ۲۱۰۰ + ۰٫۵×۷۷۰۰/۷ = ۲۶۵۰
    """
    start = date(2026, 10, 1)
    weights = [
        {
            "weight_kg": round(80 - 0.5 * (i / 7), 2),
            "logged_for_date": (start + timedelta(days=i)).isoformat(),
        }
        for i in range(days)
    ]
    r = client.post(
        "/api/v1/nutrition/weight-logs", json={"member_id": mid, "entries": weights}, headers=h
    )
    assert r.status_code == 200, r.text
    assert r.json()["logged"] == days

    food_id = FOOD_ID_HOLDER["id"]
    for i in range(days):
        day = (start + timedelta(days=i)).isoformat()
        # ۲۱۰۰ گرم از غذای ۱۰۰ کالری/۱۰۰ گرم = ۲۱۰۰ کالری
        client.post(
            "/api/v1/nutrition/food-logs",
            json={
                "member_id": mid,
                "entries": [
                    {
                        "food_id": food_id,
                        "grams": 2100,
                        "meal_slot": "lunch",
                        "logged_for_date": day,
                    }
                ],
            },
            headers=h,
        )


def test_weight_logging_is_idempotent_per_day(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    first = client.post(
        "/api/v1/nutrition/weight-logs",
        json={"member_id": mid, "entries": [{"weight_kg": 80.0, "logged_for_date": "2026-11-01"}]},
        headers=h,
    ).json()
    assert first["logged"] == 1 and first["updated"] == 0

    second = client.post(
        "/api/v1/nutrition/weight-logs",
        json={"member_id": mid, "entries": [{"weight_kg": 79.5, "logged_for_date": "2026-11-01"}]},
        headers=h,
    ).json()
    assert second["logged"] == 0 and second["updated"] == 1

    from sqlalchemy import func, select

    from db.base import get_session_factory
    from db.models import BodyWeightLog

    with get_session_factory()() as s:
        count = s.scalar(
            select(func.count()).select_from(BodyWeightLog).where(BodyWeightLog.member_id == mid)
        )
    assert count == 1, "ثبت دوبارهٔ یک روز نباید ردیف جدید بسازد"


def test_impossible_weight_is_rejected(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    r = client.post(
        "/api/v1/nutrition/weight-logs",
        json={"member_id": mid, "entries": [{"weight_kg": 400.0, "logged_for_date": "2026-11-01"}]},
        headers=h,
    )
    # اعتبارسنجی Pydantic دامنهٔ ۲۰..۴۰۰ را می‌گیرد؛ ۴۰۰ مجاز است، ۵۰۰ نه
    assert r.status_code == 200

    r2 = client.post(
        "/api/v1/nutrition/weight-logs",
        json={"member_id": mid, "entries": [{"weight_kg": 900.0, "logged_for_date": "2026-11-01"}]},
        headers=h,
    )
    assert r2.status_code == 422


def test_full_chain_recovers_known_tdee(client: TestClient) -> None:
    """زنجیرهٔ کامل DB ← موتور: TDEE باید نزدیک ۲۶۵۰ باشد."""
    h = _staff()
    mid = _member(client, h, goal="weight_loss")
    _scenario(client, h, mid)

    r = client.get(f"/api/v1/nutrition/member/{mid}/adaptive", headers=h)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["data_counts"]["weight_entries"] == 28
    assert body["data_counts"]["intake_days"] == 28
    assert body["estimate"]["data_state"] == "estimated"
    assert body["estimate"]["tdee_kcal"] == pytest.approx(2650, abs=40)
    assert body["latest_weight_kg"] == pytest.approx(78.0, abs=0.2)
    assert body["goal"] == "weight_loss"


def test_report_refuses_to_guess_without_data(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    body = client.get(f"/api/v1/nutrition/member/{mid}/adaptive", headers=h).json()

    assert body["estimate"]["tdee_kcal"] is None
    # با دادهٔ صفر، هم وزن و هم مصرف ناکافی‌اند؛ موتور اول مصرف را می‌گوید.
    # مهم این است که صریحاً «ناکافی» بگوید، نه اینکه عددی از هوا بسازد.
    assert body["estimate"]["data_state"] in ("insufficient_weight", "insufficient_intake")
    assert body["suggestion"]["action"] == "none"
    assert body["data_counts"] == {"weight_entries": 0, "intake_days": 0}


def test_target_comes_from_approved_plan(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h, goal="weight_loss")
    _scenario(client, h, mid)

    client.post(
        "/api/v1/nutrition/plans",
        json={
            "member_id": mid,
            "daily_kcal": 2100,
            "protein_g": 180,
            "carbs_g": 180,
            "fat_g": 70,
            "engine_version": "rules-1.0.0",
            "llm_explanation": "",
            "meals": [],
        },
        headers=h,
    )
    plans = client.get(f"/api/v1/nutrition/plans/member/{mid}", headers=h).json()
    plan_id = plans[-1]["id"]
    client.post(f"/api/v1/nutrition/plans/{plan_id}/approve", headers=h)

    body = client.get(f"/api/v1/nutrition/member/{mid}/adaptive", headers=h).json()

    assert body["current_target_kcal"] == 2100
    assert body["plan_id"] == plan_id
    # هدف ۲۱۰۰ با TDEE ۲۶۵۰ × ۰٫۸۵ = ۲۲۵۲ فاصله دارد، ولی گام ۱۵٪ محدود است
    adj = body["suggestion"]
    assert adj["action"] in ("increase", "keep")
    assert abs(adj["delta_kcal"]) <= round(2100 * 0.15)


def test_member_cannot_read_another_members_report(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"other-{n}", role="member")
        s.add(u)
        s.commit()
        other = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    assert client.get(f"/api/v1/nutrition/member/{mid}/adaptive", headers=other).status_code == 403


def test_member_cannot_log_weight_for_another_member(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"other2-{n}", role="member")
        s.add(u)
        s.commit()
        other = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    r = client.post(
        "/api/v1/nutrition/weight-logs",
        json={"member_id": mid, "entries": [{"weight_kg": 80.0, "logged_for_date": "2026-11-01"}]},
        headers=other,
    )
    assert r.status_code == 403

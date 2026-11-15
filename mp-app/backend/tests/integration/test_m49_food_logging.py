"""G5 — ثبت غذای روزانه: از جدول غذایی واقعی تا جمع روزانه (M49-c1)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(972001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/food.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        _seed_foods()
        yield c
    reset_engine()


def _seed_foods() -> None:
    """سه غذای واقعی از کاتالوگ MIT — اعداد دست‌نخورده."""
    from db.base import get_session_factory
    from db.models import FoodItem

    with get_session_factory()() as s:
        for row in [
            {
                "external_id": "soooolag/food-finder:سینه مرغ (پخته)",
                "name_fa": "سینه مرغ (پخته)",
                "kcal_per_100g": 165,
                "protein_g_per_100g": 31.0,
                "carbs_g_per_100g": 0.0,
                "fat_g_per_100g": 4.6,
                "category": "پروتئین حیوانی",
            },
            {
                "external_id": "soooolag/food-finder:برنج سفید (پخته)",
                "name_fa": "برنج سفید (پخته)",
                "kcal_per_100g": 130,
                "protein_g_per_100g": 2.7,
                "carbs_g_per_100g": 28.0,
                "fat_g_per_100g": 0.3,
                "category": "غلات",
            },
            {
                "external_id": "soooolag/food-finder:روغن زیتون",
                "name_fa": "روغن زیتون",
                "kcal_per_100g": 884,
                "protein_g_per_100g": 0.0,
                "carbs_g_per_100g": 0.0,
                "fat_g_per_100g": 100.0,
                "category": "روغن و چربی",
            },
        ]:
            s.add(FoodItem(**row))
        s.commit()


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


def _member(client: TestClient, h: dict) -> int:
    n = next(_counter)
    r = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"عضو {n}", "gender": "male"},
        headers=h,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def _food_id(client: TestClient, h: dict, name: str) -> int:
    rows = client.get(f"/api/v1/nutrition/foods?q={name}", headers=h).json()
    assert rows, f"غذای «{name}» در جدول نیست"
    return rows[0]["id"]


def test_food_search_returns_real_catalog_rows(client: TestClient) -> None:
    h = _staff()
    rows = client.get("/api/v1/nutrition/foods?q=مرغ", headers=h).json()

    assert len(rows) == 1
    assert rows[0]["name_fa"] == "سینه مرغ (پخته)"
    assert rows[0]["kcal_per_100g"] == 165
    assert rows[0]["protein_g_per_100g"] == 31.0


def test_logging_computes_macros_from_the_catalog(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    chicken = _food_id(client, h, "مرغ")

    r = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {"food_id": chicken, "grams": 200, "meal_slot": "lunch", "logged_for_date": "2026-11-15"}
            ],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    assert r.json()["logged"] == 1

    d = client.get(
        f"/api/v1/nutrition/food-logs/member/{mid}/daily?date=2026-11-15", headers=h
    ).json()

    # ۲۰۰ گرم = دو برابر ۱۰۰ گرم
    assert d["totals"]["kcal"] == 330.0
    assert d["totals"]["protein_g"] == 62.0
    assert d["data_state"] == "logged"
    assert d["by_slot"]["lunch"]["count"] == 1


def test_daily_totals_sum_across_slots(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    chicken = _food_id(client, h, "مرغ")
    rice = _food_id(client, h, "برنج")
    oil = _food_id(client, h, "روغن")

    client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {"food_id": chicken, "grams": 100, "meal_slot": "lunch", "logged_for_date": "2026-11-15"},
                {"food_id": rice, "grams": 200, "meal_slot": "lunch", "logged_for_date": "2026-11-15"},
                {"food_id": oil, "grams": 10, "meal_slot": "breakfast", "logged_for_date": "2026-11-15"},
            ],
        },
        headers=h,
    )

    d = client.get(
        f"/api/v1/nutrition/food-logs/member/{mid}/daily?date=2026-11-15", headers=h
    ).json()

    assert d["totals"]["kcal"] == pytest.approx(165 + 260 + 88.4, abs=0.2)
    assert d["totals"]["protein_g"] == pytest.approx(31.0 + 5.4, abs=0.2)
    assert d["by_slot"]["lunch"]["count"] == 2
    assert d["by_slot"]["breakfast"]["count"] == 1


def test_empty_day_is_declared_not_silently_zero(client: TestClient) -> None:
    """صفر باید «ثبت نشده» را بگوید، نه «نخورده» — تفاوت برای G3 حیاتی است."""
    h = _staff()
    mid = _member(client, h)

    d = client.get(
        f"/api/v1/nutrition/food-logs/member/{mid}/daily?date=2026-11-14", headers=h
    ).json()

    assert d["totals"]["kcal"] == 0
    assert d["data_state"] == "nothing_logged"
    assert "ثبت نشده" in d["reason"]


def test_invalid_entries_are_rejected_with_reasons(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    chicken = _food_id(client, h, "مرغ")

    r = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {"food_id": chicken, "grams": 100, "meal_slot": "lunch", "logged_for_date": "2026-11-15"},
                {"food_id": 999999, "grams": 100, "meal_slot": "lunch", "logged_for_date": "2026-11-15"},
            ],
        },
        headers=h,
    )

    body = r.json()
    assert body["logged"] == 1
    assert len(body["rejected"]) == 1
    assert "999999" in body["rejected"][0]["reason"]


def test_unknown_food_id_is_rejected_not_created(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)

    r = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {"food_id": 424242, "grams": 100, "meal_slot": "lunch", "logged_for_date": "2026-11-15"}
            ],
        },
        headers=h,
    )
    assert r.json()["logged"] == 0
    assert "رد شد" in r.json()["reason"]


def test_target_comes_from_approved_plan_or_says_none(client: TestClient) -> None:
    """هدف نباید از هوا ساخته شود."""
    h = _staff()
    mid = _member(client, h)

    d = client.get(f"/api/v1/nutrition/food-logs/member/{mid}/daily", headers=h).json()
    assert d["target_source"] == "none"
    assert d["target"]["kcal"] == 0

    client.post(
        "/api/v1/nutrition/plans",
        json={
            "member_id": mid,
            "daily_kcal": 2200,
            "protein_g": 160,
            "carbs_g": 220,
            "fat_g": 70,
            "engine_version": "nutrition-engine-1.0",
            "llm_explanation": "",
            "meals": [],
        },
        headers=h,
    )
    plans = client.get(f"/api/v1/nutrition/plans/member/{mid}", headers=h).json()
    plan_id = plans[-1]["id"]
    client.post(f"/api/v1/nutrition/plans/{plan_id}/approve", headers=h)

    d = client.get(f"/api/v1/nutrition/food-logs/member/{mid}/daily", headers=h).json()
    assert d["target_source"] == "approved_plan"
    assert d["target"]["kcal"] == 2200
    assert d["plan_id"] == plan_id


def test_member_cannot_log_for_another_member(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    chicken = _food_id(client, h, "مرغ")

    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"other-{n}", role="member")
        s.add(u)
        s.commit()
        other = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    r = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {"food_id": chicken, "grams": 100, "meal_slot": "lunch", "logged_for_date": "2026-11-15"}
            ],
        },
        headers=other,
    )
    assert r.status_code == 403

    r2 = client.get(f"/api/v1/nutrition/food-logs/member/{mid}/daily", headers=other)
    assert r2.status_code == 403

"""G5 — ثبت غذای روزانه: از جدول غذایی واقعی تا جمع روزانه (M49-c1)."""

from __future__ import annotations

import itertools
from pathlib import Path

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


def _member_headers(member_id: int) -> dict[str, str]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    with get_session_factory()() as s:
        member = s.get(Member, member_id)
        assert member is not None
        user = s.get(User, member.user_id)
        assert user is not None and user.role == "member"
        token = create_access_token(user.id, user.role)
    return {"Authorization": f"Bearer {token}"}


def _seed_iranian_meals() -> None:
    from db.base import get_session_factory
    from db.models import FoodItem
    from scripts.import_food_catalog import build_rows

    source = Path(__file__).resolve().parents[2] / "data" / "food" / "iranian_foods.js"
    rows = {row["name_fa"]: row for row in build_rows(source.read_text(encoding="utf-8"))}
    for name in ("قورمه سبزی", "قیمه", "آش رشته"):
        row = rows[name]
        with get_session_factory()() as s:
            s.add(
                FoodItem(
                    external_id=row["external_id"],
                    name_fa=row["name_fa"],
                    name_en=row["name_en"],
                    kcal_per_100g=row["kcal_per_100g"],
                    protein_g_per_100g=row["protein_g_per_100g"],
                    carbs_g_per_100g=row["carbs_g_per_100g"],
                    fat_g_per_100g=row["fat_g_per_100g"],
                    category=row["category"],
                )
            )
            s.commit()


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
                {
                    "food_id": chicken,
                    "grams": 200,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                }
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


def test_member_can_log_food_for_self(client: TestClient) -> None:
    staff = _staff()
    member_id = _member(client, staff)
    member = _member_headers(member_id)
    chicken = _food_id(client, member, "مرغ")

    response = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": member_id,
            "entries": [
                {
                    "food_id": chicken,
                    "grams": 150,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-16",
                }
            ],
        },
        headers=member,
    )
    assert response.status_code == 200, response.text
    assert response.json()["logged"] == 1

    daily = client.get(
        f"/api/v1/nutrition/food-logs/member/{member_id}/daily?date=2026-11-16",
        headers=member,
    )
    assert daily.status_code == 200, daily.text
    assert daily.json()["totals"]["kcal"] == 247.5
    assert daily.json()["totals"]["protein_g"] == 46.5


def test_member_can_log_three_source_iranian_meals_and_daily_totals(client: TestClient) -> None:
    staff = _staff()
    member_id = _member(client, staff)
    member = _member_headers(member_id)
    _seed_iranian_meals()

    names = ("قورمه سبزی", "قیمه", "آش رشته")
    found = {
        row["name_fa"]: row
        for name in names
        for row in client.get(f"/api/v1/nutrition/foods?q={name}", headers=member).json()
        if row["name_fa"] == name
    }
    assert set(found) == set(names)
    assert all(row["category"] == "غذای ایرانی" for row in found.values())

    amounts = {"قورمه سبزی": 150, "قیمه": 200, "آش رشته": 250}
    response = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": member_id,
            "entries": [
                {
                    "food_id": found[name]["id"],
                    "grams": grams,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-16",
                }
                for name, grams in amounts.items()
            ],
        },
        headers=member,
    )
    assert response.status_code == 200, response.text
    assert response.json()["logged"] == 3

    daily = client.get(
        f"/api/v1/nutrition/food-logs/member/{member_id}/daily?date=2026-11-16",
        headers=member,
    )
    assert daily.status_code == 200, daily.text
    body = daily.json()
    assert body["data_state"] == "logged"
    assert {row["name_fa"] for row in body["items"]} == set(names)
    assert {row["grams"] for row in body["items"]} == {150.0, 200.0, 250.0}
    assert body["totals"]["kcal"] == 975.0
    assert body["totals"]["protein_g"] == 58.0
    assert body["totals"]["carbs_g"] == 98.5
    assert body["totals"]["fat_g"] == pytest.approx(38.8, abs=0.1)


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
                {
                    "food_id": chicken,
                    "grams": 100,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                },
                {
                    "food_id": rice,
                    "grams": 200,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                },
                {
                    "food_id": oil,
                    "grams": 10,
                    "meal_slot": "breakfast",
                    "logged_for_date": "2026-11-15",
                },
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
                {
                    "food_id": chicken,
                    "grams": 100,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                },
                {
                    "food_id": 999999,
                    "grams": 100,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                },
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
                {
                    "food_id": 424242,
                    "grams": 100,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                }
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
    staff = _staff()
    owner_id = _member(client, staff)
    other_member_id = _member(client, staff)
    other = _member_headers(other_member_id)
    chicken = _food_id(client, other, "مرغ")

    response = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": owner_id,
            "entries": [
                {
                    "food_id": chicken,
                    "grams": 100,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                }
            ],
        },
        headers=other,
    )
    assert response.status_code == 403

    daily = client.get(f"/api/v1/nutrition/food-logs/member/{owner_id}/daily", headers=other)
    assert daily.status_code == 403


def test_member_cannot_create_or_approve_a_nutrition_plan(client: TestClient) -> None:
    staff = _staff()
    member_id = _member(client, staff)
    member = _member_headers(member_id)

    plan_payload = {
        "member_id": member_id,
        "daily_kcal": 2200,
        "protein_g": 150,
        "carbs_g": 250,
        "fat_g": 60,
        "engine_version": "nutrition-engine-1.0",
        "meals": [],
    }
    response = client.post("/api/v1/nutrition/plans", json=plan_payload, headers=member)
    assert response.status_code == 403

    created = client.post("/api/v1/nutrition/plans", json=plan_payload, headers=staff)
    assert created.status_code == 200, created.text
    approval = client.post(
        f"/api/v1/nutrition/plans/{created.json()['id']}/approve", headers=member
    )
    assert approval.status_code == 403


def test_dry_weight_trap_is_flagged(client: TestClient) -> None:
    """۲۵۰ گرم برنج «خشک» ≈ ۹۱۲ کالری است، نه آنچه کاربر در ذهن دارد.

    این تفاوت ۵۰۰ کالری در روز است. اگر پنهان بماند، G3 روی دادهٔ غلط
    تنظیم می‌شود. پرچم `dry_or_raw` باید در جستجو و در آیتم روز باشد.
    """
    from db.base import get_session_factory
    from db.models import FoodItem

    h = _staff()
    mid = _member(client, h)

    with get_session_factory()() as s:
        dry = FoodItem(
            external_id="test:برنج سفید (خشک)",
            name_fa="برنج سفید (خشک)",
            kcal_per_100g=365,
            protein_g_per_100g=7.0,
            carbs_g_per_100g=80.0,
            fat_g_per_100g=1.9,
            category="غلات",
        )
        s.add(dry)
        s.commit()
        dry_id = dry.id

    rows = client.get("/api/v1/nutrition/foods?q=خشک", headers=h).json()
    assert all(r["dry_or_raw"] for r in rows), "همهٔ ردیف‌های خشک باید پرچم داشته باشند"

    client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {
                    "food_id": dry_id,
                    "grams": 250,
                    "meal_slot": "lunch",
                    "logged_for_date": "2026-11-15",
                }
            ],
        },
        headers=h,
    )
    d = client.get(
        f"/api/v1/nutrition/food-logs/member/{mid}/daily?date=2026-11-15", headers=h
    ).json()

    item = d["items"][0]
    assert item["kcal"] == pytest.approx(912.5, abs=1.0)
    assert "خشک" in item["warning"]
    assert "پخته" in item["warning"]


def test_wet_food_has_no_warning(client: TestClient) -> None:
    h = _staff()
    mid = _member(client, h)
    chicken = _food_id(client, h, "مرغ")

    client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {
                    "food_id": chicken,
                    "grams": 150,
                    "meal_slot": "dinner",
                    "logged_for_date": "2026-11-15",
                }
            ],
        },
        headers=h,
    )
    d = client.get(
        f"/api/v1/nutrition/food-logs/member/{mid}/daily?date=2026-11-15", headers=h
    ).json()
    assert d["items"][0]["warning"] == ""


def test_khameh_is_not_mistaken_for_dry(client: TestClient) -> None:
    """«خامه» با «(خام)» اشتباه گرفته نمی‌شود — تله‌ی تطبیق زیررشته."""
    from modules.nutrition.service import is_dry_or_raw

    assert is_dry_or_raw("برنج سفید (خشک)") is True
    assert is_dry_or_raw("عدس (خشک)") is True
    assert is_dry_or_raw("خامه") is False
    assert is_dry_or_raw("خامه ترش") is False
    assert is_dry_or_raw("سینه مرغ (پخته)") is False

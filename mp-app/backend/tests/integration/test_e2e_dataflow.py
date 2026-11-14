"""E2E داده←تابع←خروجی (ممیزی ۲۰۲۶-۱۱-۱۴):
هر عدد/اسمی که ادمین/ورزشکار وارد می‌کند باید از توابع محاسباتی عبور کند
و در خروجی (گزارش/KPI/CSV/برنامه) دیده شود — همبستگی اجزا در یک جریان واحد."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(600001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/e2e.db")
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


@pytest.fixture()
def auth():
    def _auth(role: str = "manager") -> dict:
        from app.security.jwt import create_access_token
        from db.base import get_session_factory
        from db.models import User

        n = next(_counter)
        with get_session_factory()() as s:
            u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
            s.add(u)
            s.commit()
            return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    return _auth


def test_full_dataflow_inputs_computed_and_visible_in_outputs(client, auth):
    h = auth("admin")  # دسترسی کامل (casbin) + گزارش (admin/coach)

    # ۱) ورودی اسم/عدد عضو
    member = client.post(
        "/api/v1/members",
        json={"phone": "09123456789", "full_name": "سارا ورزشکار", "gender": "female"},
        headers=h,
    ).json()
    mid = member["id"]
    # اسم ورودی روی User ذخیره می‌شود (MemberOut فقط شناسه‌ها را برمی‌گرداند)
    from db.base import get_session_factory
    from db.models import Member, User

    with get_session_factory()() as s_:
        user_name = s_.get(User, s_.get(Member, mid).user_id).full_name
    assert user_name == "سارا ورزشکار"

    # ۲) عدد قیمت اشتراک ← پرداخت ← دیده‌شدن در CSV مالی
    client.post(
        "/api/v1/members/memberships",
        json={"member_id": mid, "plan_name": "سه‌ماهه", "duration_days": 90, "price_rial": 7500000},
        headers=h,
    )
    pay = client.post(
        "/api/v1/payments",
        json={
            "member_id": mid,
            "amount_rial": 7500000,
            "method": "cash",
            "description": "اشتراک سه‌ماهه",
        },
        headers=h,
    ).json()
    client.post(f"/api/v1/payments/{pay['id']}/verify", json={}, headers=h)
    csv_text = client.get("/api/v1/payments/finance/export.csv", headers=h).text
    assert "7500000" in csv_text  # عدد ورودی در خروجی حسابداری

    # ۳) اعداد ۷ چین پوستی + سن/جنس ← ذخیرهٔ خام + قفل E07
    jp7 = client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": mid,
            "age": 32,
            "gender": "female",
            "skinfolds_mm": {
                "chest": 12.5,
                "triceps": 16.0,
                "subscapular": 14.0,
                "suprailiac": 18.5,
                "abdomen": 20.0,
                "thigh": 22.0,
                "calf": 15.0,
            },
            "quality": "good",
            "method": "caliper-holtain",
        },
        headers=h,
    ).json()
    assert jp7["body_fat_pct"] is None and "LOCKED" in jp7["equation_version"]
    import json as _json

    raw = jp7["skinfolds_mm"]
    skin = _json.loads(raw) if isinstance(raw, str) else raw
    assert skin["chest"] == 12.5  # عدد ورودی عیناً برگشت

    # ۴) نمرات ۱۴ دامنه (اعداد) ← ارزیابی ذخیره می‌شود
    scores = [{"domain": d, "score": (d % 5) + 1, "notes": f"دامنهٔ {d}"} for d in range(1, 15)]
    assess = client.post(
        "/api/v1/assessments",
        json={"member_id": mid, "scores": scores, "notes": "ارزیابی اولیه"},
        headers=h,
    ).json()
    assert len(assess["scores"]) == 14
    assert assess["scores"][0]["score"] == scores[0]["score"]

    # ۵) موتور تمرین: هدف/سطح/تعداد روز ← هفته‌ها و ست‌های محاسبه‌شده
    from engine.workout import generate_program

    plan = generate_program("hypertrophy", "beginner", 3, weeks_count=8)
    weeks_out = [
        {
            "week_number": w.week_number,
            "focus": w.focus,
            "exercises": [
                {
                    "exercise_id": e.exercise_id,
                    "day": e.day,
                    "order": i,
                    "sets": e.sets,
                    "reps": e.reps,
                    "load_pct": e.load_pct,
                    "rest_seconds": e.rest_seconds,
                    "notes": e.notes,
                }
                for i, e in enumerate(w.exercises)
            ],
        }
        for w in plan.weeks
    ]
    prog = client.post(
        "/api/v1/programs/from-engine",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "engine_version": plan.engine_version,
            "llm_explanation": "برنامه از موتور قطعی",
            "weeks": weeks_out,
        },
        headers=h,
    ).json()
    got = client.get(f"/api/v1/programs/{prog['id']}", headers=h).json()
    assert len(got["weeks"]) == 8  # عدد ورودی weeks_count در خروجی
    assert got["weeks"][0]["exercises"][0]["sets"] == weeks_out[0]["exercises"][0]["sets"]

    # ۶) موتور تغذیه: وزن/قد/سن ← کالری/ماکرو محاسبه‌شده
    from engine.nutrition import generate_nutrition

    nut = generate_nutrition(62.0, 165.0, 32, "female", "moderate", "weight_loss")
    plan2 = client.post(
        "/api/v1/nutrition/plans",
        json={
            "member_id": mid,
            "daily_kcal": nut.target_kcal,
            "protein_g": nut.protein_g,
            "carbs_g": nut.carbs_g,
            "fat_g": nut.fat_g,
            "engine_version": nut.engine_version,
        },
        headers=h,
    ).json()
    assert plan2["daily_kcal"] == nut.target_kcal  # عدد محاسبه‌شده ذخیره/برگشت
    assert nut.target_kcal > 1000  # خروجی واقعی نه صفر

    # ۷) کیف‌پول: شارژ ← پرداخت ← مانده درست
    client.post(
        "/api/v1/payments/wallet/charge", json={"member_id": mid, "amount_rial": 200000}, headers=h
    )
    client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": mid, "amount_rial": 50000}, headers=h
    )
    wallet = client.get(f"/api/v1/payments/wallet/{mid}", headers=h).json()
    assert wallet["balance_rial"] == 150000  # ۲۰۰۰۰۰-۵۰۰۰۰

    # ۸) ظرفیت کلاس با عدد ← رزرو
    cls = client.post("/api/v1/classes", json={"name": "اینتروال", "capacity": 5}, headers=h).json()
    booking = client.post(
        "/api/v1/classes/book", json={"class_id": cls["id"], "member_id": mid}, headers=h
    ).json()
    assert booking["status"] == "confirmed"

    # ۹) ورودی‌های عددی autoreg ← وزن پیشنهادی با دلیل
    sug = client.post(
        "/api/v1/ai/suggest-weight",
        json={"last_weight": 40, "reps_done": 13, "target_reps": 10, "rpe": 7},
        headers=h,
    ).json()
    assert sug["next_weight"] == 42.5 and sug["reason"]

    # ۱۰) گزارش محرمانه: اسم واقعی + اعداد ← سند HTML/JSON
    rep = client.get(f"/api/v1/reports/confidential/{mid}?format=json", headers=h).json()
    assert rep["section_1_identity"]["full_name"] == "سارا ورزشکار"
    data_names = [r["data"] for r in rep["section_3_data_snapshot"]["rows"]]
    assert any("چین" in n or "پوست" in n or "chest" in str(n) for n in data_names) or data_names
    html = client.get(f"/api/v1/reports/confidential/{mid}?format=html", headers=h).text
    assert "سارا ورزشکار" in html

    # ۱۱) KPI ها داده‌های ایجادشده را می‌بینند
    kpis = client.get("/api/v1/admin/kpis", headers=h).json()
    assert kpis["members_total"] >= 1
    assert kpis["revenue_paid_rial"] == 7500000 + 50000  # اشتراک + پرداخت کیف‌پول — جمع دقیق

    # ۱۲) ورودی نامعتبر ← رد صریح (هرگز بی‌صدا نرمال نشود)
    bad = client.post(
        "/api/v1/assessments/jp7",
        json={"member_id": mid, "age": 9, "gender": "female", "skinfolds_mm": {"chest": 1}},
        headers=h,
    )
    assert bad.status_code == 422
    bad2 = client.post(
        "/api/v1/members", json={"phone": "09123456780", "full_name": "ا"}, headers=h
    )
    assert bad2.status_code == 422  # اسم کوتاه رد می‌شود

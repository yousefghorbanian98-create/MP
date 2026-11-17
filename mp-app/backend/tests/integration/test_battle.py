"""M14 — تست نبرد: مسیر طلایی کامل + لبه‌ها (رشتهٔ بلند، عدد منفی، تایپ غلط)."""

from __future__ import annotations

import itertools
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path) -> Generator[TestClient, None, None]:
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    settings.database_url = f"sqlite:///{tmp_path / 'battle.db'}"
    reset_engine()
    init_db()
    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()


def _staff(client: TestClient, role: str = "manager") -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_staff.counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        token = create_access_token(u.id, u.role)
    return {"Authorization": f"Bearer {token}"}


_staff.counter = itertools.count(int(__import__("time").time() * 1000) % 10**8)


def test_golden_path_battle(client):
    """مسیر طلایی کامل: ورود → عضو → اشتراک → ارزیابی JP7 → برنامه (G8) → چک‌این → پرداخت."""
    h = _staff(client)
    # عضو
    member = client.post(
        "/api/v1/members/",
        json={"phone": "09123334444", "full_name": "نبرد طلایی", "gender": "male"},
        headers=h,
    ).json()
    mid = member["id"]
    # اشتراک فعال
    sub = client.post(
        "/api/v1/members/memberships",
        json={"member_id": mid, "plan_name": "سالانه", "duration_days": 365, "price_rial": 5000000},
        headers=h,
    )
    assert sub.status_code == 200, sub.text
    assert sub.json()["status"] == "active"
    # ارزیابی JP7 (فرمول قطعی)
    assess = client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": mid,
            "age": 30,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10,
                "triceps": 8,
                "subscapular": 10,
                "suprailiac": 9,
                "abdomen": 15,
                "thigh": 12,
                "calf": 7,
            },
        },
        headers=h,
    )
    assert assess.status_code == 200, assess.text
    # E07/D-012: درصد چربی قفل — خام ذخیره، محاسبه ممنوع
    assert assess.json()["body_fat_pct"] is None
    assert assess.json()["equation_version"].startswith("LOCKED")
    # برنامه از خروجی موتور قطعی (G8) — draft سپس تأیید مربی
    engine_out = {
        "member_id": mid,
        "goal": "hypertrophy",
        "engine_version": "1.0.0",
        "llm_explanation": "برنامهٔ ۸ هفته‌ای هایپرتروفی با progression خطی.",  # فقط متن (G8)
        "weeks": [
            {
                "week_number": 1,
                "focus": "hypertrophy",
                "exercises": [
                    {
                        "exercise_id": 1,
                        "day": 1,
                        "order": 0,
                        "sets": 3,
                        "reps": "8-12",
                        "load_pct": 70,
                        "rest_seconds": 90,
                        "notes": "",
                    },
                    {
                        "exercise_id": 2,
                        "day": 1,
                        "order": 1,
                        "sets": 3,
                        "reps": "10",
                        "load_pct": 65,
                        "rest_seconds": 60,
                        "notes": "",
                    },
                ],
            }
        ],
    }
    program = client.post("/api/v1/programs/from-engine", json=engine_out, headers=h)
    assert program.status_code == 200, program.text
    assert program.json()["status"] == "draft"
    assert program.json()["weeks"][0]["exercises"][0]["load_pct"] == 70
    approve = client.post(f"/api/v1/programs/{program.json()['id']}/approve", headers=h)
    assert approve.status_code == 200
    assert approve.json()["status"] == "approved"
    # چک‌این (عضو فعال → ok)
    ci = client.post("/api/v1/face/checkin", json={"member_id": mid, "method": "qr"}, headers=h)
    assert ci.status_code == 200, ci.text
    assert ci.json()["result"] == "ok"
    # پرداخت + تأیید رسید
    pay = client.post(
        "/api/v1/payments",
        json={"member_id": mid, "amount_rial": 5000000, "method": "cash"},
        headers=h,
    )
    assert pay.status_code == 200, pay.text
    receipt = client.post(
        f"/api/v1/payments/{pay.json()['id']}/verify",
        json={"reference_id": "BATTLE-001"},
        headers=h,
    )
    assert receipt.status_code == 200, receipt.text
    assert receipt.json()["status"] == "paid"


def test_edge_long_name_rejected(client):
    h = _staff(client)
    resp = client.post(
        "/api/v1/members/",
        json={"phone": "09123335555", "full_name": "ن", "gender": "male" * 300},
        headers=h,
    )
    assert resp.status_code == 422  # max_length name


def test_edge_negative_amount_rejected(client):
    h = _staff(client)
    member = client.post(
        "/api/v1/members/",
        json={"phone": "09123336666", "full_name": "منفی", "gender": "male"},
        headers=h,
    ).json()
    # قیمت منفی اشتراک
    r1 = client.post(
        "/api/v1/members/memberships",
        json={
            "member_id": member["id"],
            "plan_name": "ماهانه",
            "duration_days": 30,
            "price_rial": -5,
        },
        headers=h,
    )
    assert r1.status_code == 422
    # مبلغ پرداخت زیر کف
    r2 = client.post(
        "/api/v1/payments",
        json={"member_id": member["id"], "amount_rial": -100, "method": "cash"},
        headers=h,
    )
    assert r2.status_code == 422


def test_edge_wrong_types_rejected(client):
    h = _staff(client)
    resp = client.post("/api/v1/members/", json={"phone": 912345, "full_name": ["لیست"]}, headers=h)
    assert resp.status_code == 422
    resp2 = client.post("/api/v1/face/checkin", json={"member_id": "x", "method": "qr"}, headers=h)
    assert resp2.status_code == 422


def test_edge_bad_method_and_denied_checkin(client):
    h = _staff(client)
    # متد غیرمجاز
    resp = client.post("/api/v1/face/checkin", json={"member_id": 1, "method": "hack"}, headers=h)
    assert resp.status_code == 422
    # عضو بدون اشتراک → denied
    member = client.post(
        "/api/v1/members/",
        json={"phone": "09123338888", "full_name": "بدون اشتراک", "gender": "male"},
        headers=h,
    ).json()
    ci = client.post(
        "/api/v1/face/checkin", json={"member_id": member["id"], "method": "manual"}, headers=h
    )
    assert ci.status_code == 200
    assert ci.json()["result"] == "denied"


def test_assessment_wrong_input_rejected(client):
    h = _staff(client)
    resp = client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": 1,
            "age": -5,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10,
                "triceps": 8,
                "subscapular": 10,
                "suprailiac": 9,
                "abdomen": 15,
                "thigh": 12,
                "calf": 7,
            },
        },
        headers=h,
    )
    assert resp.status_code == 422  # age منفی
    resp2 = client.post(
        "/api/v1/assessments/jp7",
        json={"member_id": 1, "age": 30, "gender": "alien", "skinfolds_mm": {"chest": 10}},
        headers=h,
    )
    assert resp2.status_code == 422  # جنسیت نامعتبر

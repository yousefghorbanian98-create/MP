"""تست‌های یکپارچهٔ ai_engine (M15) — مسیر API تا draft با حفظ G8."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    settings.database_url = f"sqlite:///{tmp_path / 'ai.db'}"
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


def _member(client, h) -> int:
    return client.post(
        "/api/v1/members/",
        json={"phone": "09125550001", "full_name": "عضو هوش مصنوعی", "gender": "male"},
        headers=h,
    ).json()["id"]


def test_program_generate_draft_and_g8(client):
    from engine.workout import RULES

    h = _staff(client)
    mid = _member(client, h)
    resp = client.post(
        "/api/v1/ai/program/generate",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "level": "beginner",
            "days_per_week": 3,
            "weeks_count": 4,
            "constraints": ["knee"],
        },
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "draft"
    assert isinstance(body["llm_explanation"], str) and body["llm_explanation"]  # فقط متن
    # گیت G8: اعداد ذخیره‌شده = جدول قواعد
    rule = RULES[("hypertrophy", "beginner")]
    ex0 = body["weeks"][0]["exercises"][0]
    assert ex0["sets"] == rule["sets"]
    assert ex0["reps"] == rule["reps"]
    assert ex0["rest_seconds"] == rule["rest"]
    # محدودیت زانو → اسکوات نیست
    names = [e["notes"] for w in body["weeks"] for e in w["exercises"]]
    assert any("knee" in (n or "") for n in names)


def test_nutrition_generate_draft(client):
    h = _staff(client)
    mid = _member(client, h)
    resp = client.post(
        "/api/v1/ai/nutrition/generate",
        json={
            "member_id": mid,
            "goal": "weight_loss",
            "activity": "light",
            "weight_kg": 85,
            "height_cm": 175,
            "age": 35,
            "gender": "male",
        },
        headers=h,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "draft"
    # TDEE قطعی (Mifflin): محاسبه درون‌کد تا ادعای ریاضی نماند
    bmr = 10 * 85 + 6.25 * 175 - 5 * 35 + 5
    assert body["daily_kcal"] == round(round(bmr * 1.375) * 0.85)
    assert body["protein_g"] > 0 and body["carbs_g"] > 0 and body["fat_g"] > 0


def test_generate_member_only_for_self(client):
    """D-005 (2026-11-15 — تغییر معنای عمدی): عضو می‌تواند برنامهٔ خودش را از فرم ورودی بسازد
    (draft — همچنان نیازمند تأیید کادر)، اما برای دیگری نه. قبل از این تغییر، عضو کلاً ۴۰۳
    می‌گرفت که با فرم ورودی کلاینت (intake) ناسازگار بود — باگ REA-2026-11-15."""
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_staff.counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name="member-self", role="member")
        s.add(u)
        s.flush()
        m = Member(user_id=u.id, gender="male")
        s.add(m)
        s.commit()
        own_id, other_id = m.id, 99999
    from app.security.jwt import create_access_token

    h = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    # برای خودش: مجاز (draft)
    resp = client.post(
        "/api/v1/ai/program/generate",
        json={"member_id": own_id, "goal": "fitness", "level": "beginner", "days_per_week": 3},
        headers=h,
    )
    assert resp.status_code == 200, resp.text

    # برای دیگری: ممنوع (مالکیت)
    resp = client.post(
        "/api/v1/ai/program/generate",
        json={"member_id": other_id, "goal": "fitness", "level": "beginner", "days_per_week": 3},
        headers=h,
    )
    assert resp.status_code == 403

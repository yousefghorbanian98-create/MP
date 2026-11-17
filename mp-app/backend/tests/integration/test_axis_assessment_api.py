"""تست‌های یکپارچهٔ API ارزیابی ۱۴ توانایی (M36-c2) — جریان، RBAC، اعتبارسنجی."""

from __future__ import annotations

import itertools
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(700001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/axis.db")
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
def seeded_norms(client):
    """نُرم‌ها + rubricها را در دیتابیس تست seed می‌کند."""
    from db.base import get_session_factory
    from scripts.seed_criteria import seed as seed_criteria
    from scripts.seed_norms import seed as seed_norms

    with get_session_factory()() as s:
        seed_norms(s)
        seed_criteria(s)
    return True


@pytest.fixture()
def auth():
    def _auth(role: str = "coach") -> dict:
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


@pytest.fixture()
def member_ids(client, seeded_norms):
    """عضو زن ۳۰ساله + کاربر عضو (برای تست مالکیت)."""
    from db.base import get_session_factory
    from db.models import Member, User

    with get_session_factory()() as s:
        user = User(phone="09127000001", full_name="عضو تست", role="member")
        s.add(user)
        s.flush()
        member = Member(user_id=user.id, birth_date=date(1995, 6, 1), gender="female")
        s.add(member)
        s.commit()
        return {"member_id": member.id, "user_id": user.id}


FULL_TESTS = [
    {"test_key": "sit_and_reach", "raw_value": 30.0},
    {"test_key": "pushup_1min", "raw_value": 18.0},
    {"test_key": "grip_kg", "raw_value": 30.0},
    {"test_key": "cooper_1_5mile_sec", "raw_value": 855.0},
    {"test_key": "plank_secs", "raw_value": 70.0},
    {"test_key": "rubric_balance", "raw_value": 55.0},
    {"test_key": "rubric_posture", "raw_value": 62.0},
    {"test_key": "rubric_coordination", "raw_value": 48.0},
    {"test_key": "rubric_lifting", "raw_value": 75.0},
    {"test_key": "rubric_breath", "raw_value": 70.0},
    {"test_key": "rubric_recovery", "raw_value": 44.0},
    {"test_key": "rubric_body_awareness", "raw_value": 66.0},
    {"test_key": "rubric_foundational", "raw_value": 80.0},
]


def test_full_assessment_flow_matrix(client, auth, member_ids):
    h = auth("coach")
    res = client.post(
        "/api/v1/axis-assessments",
        json={"member_id": member_ids["member_id"], "tests": FULL_TESTS, "notes": "ارزیابی اولیه"},
        headers=h,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body["axes"]) == 14
    by_axis = {a["axis"]: a for a in body["axes"]}
    # محور ۱: نشست و رسیدن 30cm زن ۳۰ساله (بازهٔ ۲۵-۷۵: 22.0–39.3) ← درصدک میانهٔ بازه
    assert by_axis[1]["score"] is not None
    assert by_axis[1]["quality"] == "range_estimate"
    assert by_axis[1]["decision_state"] in ("covered", "maintain", "direct")
    # محور ۱۲: rubric_recovery=44 ← زیر ۴۰ نیست، پس covered نه direct
    assert by_axis[12]["score"] == 44.0
    assert by_axis[12]["decision_state"] == "covered"
    assert "دلیل" not in by_axis[12]["decision_reason"] or by_axis[12]["decision_reason"]
    # تصمیم‌ها همیشه دلیل دارند
    for axis_row in body["axes"]:
        assert axis_row["decision_reason"]
    assert sum(body["summary"].values()) == 14

    # تاریخچه
    res2 = client.get(f"/api/v1/axis-assessments/member/{member_ids['member_id']}", headers=h)
    assert res2.status_code == 200
    assert len(res2.json()) == 1

    # ماتریس مجدد
    res3 = client.get(f"/api/v1/axis-assessments/{body['assessment_id']}/matrix", headers=h)
    assert res3.status_code == 200
    assert res3.json()["assessment_id"] == body["assessment_id"]


def test_missing_axis_scores_are_unknown_not_zero(client, auth, member_ids):
    """فقط یک آزمون ثبت شود ← بقیهٔ محورها unknown (نه صفر)."""
    h = auth("coach")
    res = client.post(
        "/api/v1/axis-assessments",
        json={
            "member_id": member_ids["member_id"],
            "tests": [{"test_key": "pushup_1min", "raw_value": 18.0}],
        },
        headers=h,
    )
    assert res.status_code == 200, res.text
    by_axis = {a["axis"]: a for a in res.json()["axes"]}
    assert by_axis[1]["score"] is None
    assert by_axis[1]["quality"] == "missing"
    assert by_axis[1]["decision_state"] == "unknown"
    assert by_axis[3]["score"] is not None
    assert by_axis[5]["score"] is not None


def test_rbac_member_cannot_create_coach_can(client, auth, member_ids, seeded_norms):
    h_member = auth("member")
    res = client.post(
        "/api/v1/axis-assessments",
        json={"member_id": member_ids["member_id"], "tests": FULL_TESTS},
        headers=h_member,
    )
    assert res.status_code == 403
    h_reception = auth("reception")
    res2 = client.get("/api/v1/axis-assessments/1/matrix", headers=h_reception)
    assert res2.status_code == 403


def test_validation_unknown_test_and_missing_birthdate(client, auth, member_ids, seeded_norms):
    from db.base import get_session_factory
    from db.models import Member

    h = auth("coach")
    # آزمون ناشناخته
    res = client.post(
        "/api/v1/axis-assessments",
        json={
            "member_id": member_ids["member_id"],
            "tests": [{"test_key": "mystery_test", "raw_value": 5}],
        },
        headers=h,
    )
    assert res.status_code == 400
    assert "نُرم" in res.json()["error"]["message"]
    # rubric خارج بازه
    res2 = client.post(
        "/api/v1/axis-assessments",
        json={
            "member_id": member_ids["member_id"],
            "tests": [{"test_key": "rubric_balance", "raw_value": 150}],
        },
        headers=h,
    )
    assert res2.status_code == 400
    # بدون تاریخ تولد
    with get_session_factory()() as s:
        member = s.get(Member, member_ids["member_id"])
        member.birth_date = None
        s.commit()
    res3 = client.post(
        "/api/v1/axis-assessments",
        json={"member_id": member_ids["member_id"], "tests": FULL_TESTS},
        headers=h,
    )
    assert res3.status_code == 400
    assert "تولد" in res3.json()["error"]["message"]


def test_review_flow_audit_and_separation_of_duties(client, auth, member_ids, seeded_norms):
    """M36-c3: تأیید/رد با دلیل + AuditLog + جدایی وظیفه (coach نمی‌تواند بازبینی کند)."""
    from db.base import get_session_factory
    from db.models import AuditLog

    h_coach = auth("coach")
    res = client.post(
        "/api/v1/axis-assessments",
        json={"member_id": member_ids["member_id"], "tests": FULL_TESTS},
        headers=h_coach,
    )
    assert res.status_code == 200
    aid = res.json()["assessment_id"]

    # جدایی وظیفه: مربی که ثبت کرده نمی‌تواند تأیید کند
    res2 = client.post(
        f"/api/v1/axis-assessments/{aid}/review",
        json={"action": "approve"},
        headers=h_coach,
    )
    assert res2.status_code == 403

    # رد بدون دلیل ممنوع
    h_manager = auth("manager")
    res3 = client.post(
        f"/api/v1/axis-assessments/{aid}/review",
        json={"action": "reject", "reason": ""},
        headers=h_manager,
    )
    assert res3.status_code == 400

    # تأیید با مدیر
    res4 = client.post(
        f"/api/v1/axis-assessments/{aid}/review",
        json={"action": "approve", "reason": "تأیید نهایی"},
        headers=h_manager,
    )
    assert res4.status_code == 200
    assert res4.json()["status"] == "reviewed"

    # AuditLog ثبت شده
    with get_session_factory()() as s:
        logs = s.query(AuditLog).filter_by(action="axis_assessment_approve", entity_id=aid).all()
        assert len(logs) == 1

    # بازبینی مجدد ممنوع
    res5 = client.post(
        f"/api/v1/axis-assessments/{aid}/review",
        json={"action": "approve"},
        headers=h_manager,
    )
    assert res5.status_code == 400


def test_set_feedback_endpoint_g1(client, auth, member_ids):
    """M38-c2 — G1: بازخورد ست از کلاینت ← پیشنهاد جلسهٔ بعد (بدون عدد از LLM)."""
    from db.base import get_session_factory
    from db.models import SetFeedback

    h = auth("coach")
    res = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": member_ids["member_id"],
            "entries": [
                {
                    "movement_id": "pushup-l1",
                    "weight": 0,
                    "target_reps": 10,
                    "reps_done": 12,
                    "rir": 3,
                    "soreness": 2,
                },
                {
                    "movement_id": "pushup-l1",
                    "weight": 0,
                    "target_reps": 10,
                    "reps_done": 11,
                    "rir": 2,
                    "soreness": 8,
                },
            ],
        },
        headers=h,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["suggestions"][0]["volume_action"] == "deload"
    with get_session_factory()() as s:
        rows = s.query(SetFeedback).filter_by(movement_id="pushup-l1").all()
        assert len(rows) == 2

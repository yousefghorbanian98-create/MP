"""M48-c1 — G1 کامل: پیشنهاد بازخورد ست باید واقعاً به هفتهٔ بعد اعمال شود.

پیش از این، `POST /programs/set-feedback` بازخورد را ذخیره می‌کرد و یک
پیشنهاد برمی‌گرداند، ولی **هیچ‌چیز تغییر نمی‌کرد**. یعنی حلقهٔ بازخورد
نیمه‌کاره بود: سیستم حرف می‌زد، گوش نمی‌داد.

این تست‌ها زنجیرهٔ کامل را قفل می‌کنند:
  ست ثبت می‌شود → پیشنهاد وزن/حجم ← هفتهٔ بعد با همان اعداد به‌روز می‌شود
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(970001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/fb.db")
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
        u = User(phone=f"09{n:09d}", full_name=f"coach-{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _member_with_program(client: TestClient, h: dict) -> tuple[int, int]:
    n = next(_counter)
    m = client.post(
        "/api/v1/members",
        json={"phone": f"09{n:09d}", "full_name": f"عضو {n}", "gender": "male"},
        headers=h,
    )
    assert m.status_code in (200, 201), m.text
    mid = m.json()["id"]
    p = client.post(
        "/api/v1/ai/program/generate",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "level": "beginner",
            "days_per_week": 3,
            "weeks_count": 4,
            "constraints": [],
        },
        headers=h,
    )
    assert p.status_code == 200, p.text
    return mid, p.json()["id"]


def _week_rows(program_id: int, week_number: int) -> list[dict]:
    from db.base import get_session_factory
    from db.models import ProgramExercise, ProgramWeek

    with get_session_factory()() as s:
        w = (
            s.query(ProgramWeek)
            .filter(ProgramWeek.program_id == program_id, ProgramWeek.week_number == week_number)
            .first()
        )
        if w is None:
            return []
        return [
            {"exercise_id": e.exercise_id, "sets": e.sets, "load_pct": e.load_pct, "order": e.order}
            for e in s.query(ProgramExercise)
            .filter(ProgramExercise.week_id == w.id)
            .order_by(ProgramExercise.id)
            .all()
        ]


def test_high_soreness_reduces_next_week_sets(client: TestClient) -> None:
    """درد ≥ ۷ ⇒ یک ست کمتر در هفتهٔ بعد — نه فقط در پاسخ JSON."""
    h = _staff()
    mid, pid = _member_with_program(client, h)
    before = _week_rows(pid, 2)
    assert before, "هفتهٔ دوم باید از قبل وجود داشته باشد"
    from engine.feedback_apply import resolve_exercise_id

    squat_id = resolve_exercise_id("back_squat")
    target = next(r for r in before if r["exercise_id"] == squat_id)
    r = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "program_id": pid,
            "entries": [
                {
                    "movement_id": "back_squat",
                    "weight": 60,
                    "target_reps": 10,
                    "reps_done": 8,
                    "rir": 0,
                    "soreness": 8,
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["suggestions"][0]["volume_action"] == "deload"
    assert body["applied"]["weeks_updated"] >= 1

    after = _week_rows(pid, 2)
    after_row = next(a for a in after if a["exercise_id"] == target["exercise_id"])
    assert after_row["sets"] == max(1, target["sets"] - 1), (
        f"ست‌ها باید از {target['sets']} به {target['sets'] - 1} کاهش می‌یافت، "
        f"ولی {after_row['sets']} است"
    )


def test_heavy_rir_increases_next_week_load(client: TestClient) -> None:
    """RIR ≥ ۲ (ست راحت) ⇒ بار بیشتر در هفتهٔ بعد."""
    h = _staff()
    mid, pid = _member_with_program(client, h)
    before = _week_rows(pid, 2)
    from engine.feedback_apply import resolve_exercise_id

    squat_id = resolve_exercise_id("back_squat")
    target = next(r for r in before if r["exercise_id"] == squat_id)

    r = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "program_id": pid,
            "entries": [
                {
                    "movement_id": "back_squat",
                    "weight": 60,
                    "target_reps": 8,
                    "reps_done": 12,
                    "rir": 3,
                    "soreness": 2,
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    sugg = r.json()["suggestions"][0]
    assert sugg["volume_action"] == "keep"
    assert sugg["next_weight"] > 60

    after = _week_rows(pid, 2)
    after_row = next(a for a in after if a["exercise_id"] == target["exercise_id"])
    assert after_row["load_pct"] > target["load_pct"], (
        "بار نسبی هفتهٔ بعد باید بیشتر شود، چون ست راحت ثبت شده"
    )


def test_week_one_never_changes(client: TestClient) -> None:
    """هفتهٔ ۱ گذشته است — بازنویسی آن تاریخ را جعل می‌کند."""
    h = _staff()
    mid, pid = _member_with_program(client, h)
    w1_before = _week_rows(pid, 1)

    client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "program_id": pid,
            "entries": [
                {
                    "movement_id": "back_squat",
                    "weight": 60,
                    "target_reps": 10,
                    "reps_done": 10,
                    "rir": 2,
                    "soreness": 5,
                }
            ],
        },
        headers=h,
    )
    assert _week_rows(pid, 1) == w1_before


def test_unknown_movement_is_reported_not_ignored(client: TestClient) -> None:
    """حرکت ناشناخته باید صریح گزارش شود، نه بی‌صدا رد."""
    h = _staff()
    mid, pid = _member_with_program(client, h)

    r = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "program_id": pid,
            "entries": [
                {
                    "movement_id": "not_a_real_movement",
                    "weight": 50,
                    "target_reps": 10,
                    "reps_done": 10,
                    "rir": 2,
                    "soreness": 1,
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 200
    applied = r.json()["applied"]
    assert "not_a_real_movement" in applied["unmatched_movements"]
    assert applied["weeks_updated"] == 0


def test_single_reported_set_does_not_collapse_prescribed_sets(client: TestClient) -> None:
    """باگ ۲۰ — یک ست گزارش‌شده نباید برنامهٔ ۳ ستی را به ۱ ست برساند.

    عضو فقط ۱ ست از ۳ ست را گزارش می‌کند (فراموشی، نه واقعیت). موتور نباید
    از «تعداد ردیف» عدد حجم بسازد و آن را روی برنامه بنشاند.
    """
    h = _staff()
    mid, pid = _member_with_program(client, h)
    before = _week_rows(pid, 2)

    from engine.feedback_apply import resolve_exercise_id

    squat_id = resolve_exercise_id("back_squat")
    target = next(r for r in before if r["exercise_id"] == squat_id)

    r = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "program_id": pid,
            "entries": [
                {
                    "movement_id": "back_squat",
                    "weight": 60,
                    "target_reps": 10,
                    "reps_done": 10,
                    "rir": 2,
                    "soreness": 2,
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    sugg = r.json()["suggestions"][0]

    assert sugg["volume_action"] == "keep"
    # هیچ `sets_done`ای گزارش نشده ⇒ هیچ عدد حجمی نباید اعلام شود
    assert sugg["next_sets"] is None, "عدد حجم ساختگی از تعداد ردیف‌ها ساخته شد"

    after = _week_rows(pid, 2)
    after_row = next(a for a in after if a["exercise_id"] == squat_id)
    assert after_row["sets"] == target["sets"], (
        f"برنامهٔ {target['sets']} ستی نباید به {after_row['sets']} ست تغییر کند"
    )


def test_explicit_sets_done_is_honoured(client: TestClient) -> None:
    """اگر عضو خودش `sets_done` بدهد، همان عدد (کاهش واقعی) اعمال می‌شود."""
    h = _staff()
    mid, pid = _member_with_program(client, h)
    before = _week_rows(pid, 2)

    from engine.feedback_apply import resolve_exercise_id

    squat_id = resolve_exercise_id("back_squat")
    target = next(r for r in before if r["exercise_id"] == squat_id)
    assert target["sets"] > 2, "برای این تست به برنامه‌ای با بیش از ۲ ست نیاز است"

    r = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": mid,
            "program_id": pid,
            "entries": [
                {
                    "movement_id": "back_squat",
                    "weight": 60,
                    "target_reps": 10,
                    "reps_done": 10,
                    "rir": 2,
                    "soreness": 2,
                    "sets_done": target["sets"] - 2,
                }
            ],
        },
        headers=h,
    )
    assert r.status_code == 200, r.text
    sugg = r.json()["suggestions"][0]
    assert sugg["next_sets"] == target["sets"] - 2

    after = _week_rows(pid, 2)
    after_row = next(a for a in after if a["exercise_id"] == squat_id)
    assert after_row["sets"] == target["sets"] - 2

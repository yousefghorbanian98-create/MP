"""Q7 — دروازهٔ ایمنی هنگام ساخت برنامه.

کشف مهم این چرخه: `engine/safety.py` از قبل پروتکل سالمند (D-016) را
داشت؛ بازنویسی کاملش آن را نابود می‌کرد. حالا هر دو دامنه در یک ماژول
زنده‌اند و این تست‌ها رفتار دروازه را در مسیر واقعی ساخت برنامه می‌سنجند.
"""

from __future__ import annotations

import itertools
import json

import pytest

from app.config import settings

_counter = itertools.count(978001)


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/safety.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    yield
    reset_engine()


def _member(constraints: str) -> int:
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"m{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, gender="male", goal="x", constraints=constraints, branch_id=1)
        s.add(m)
        s.commit()
        return m.id


def _program(member_id: int, movement: str):
    from db.base import get_session_factory
    from modules.programs.service import create_program_from_engine_output

    with get_session_factory()() as s:
        return create_program_from_engine_output(
            s,
            member_id,
            {
                "goal": "hypertrophy",
                "engine_version": "test",
                "weeks": [
                    {
                        "week_number": 1,
                        "exercises": [
                            {
                                "exercise_id": 1,
                                "day": 1,
                                "order": 0,
                                "sets": 3,
                                "reps": "8-12",
                                "movement": movement,
                            }
                        ],
                    }
                ],
            },
        )


def test_contraindicated_program_is_flagged(db) -> None:
    mid = _member('["knee_injury"]')
    program = _program(mid, "squat")

    flags = json.loads(program.safety_flags)
    assert flags["status"] == "blocked"
    assert flags["blocked"][0]["constraint"] == "knee_injury"
    assert "squat" in flags["blocked"][0]["blocked_exercises"]
    assert flags["safe_to_generate"] is False


def test_program_without_contraindication_is_recorded(db) -> None:
    mid = _member("[]")
    program = _program(mid, "bench_press")

    flags = json.loads(program.safety_flags)
    # «محدودیتی ثبت نشده» یعنی نامعلوم، نه بی‌خطر
    assert flags["status"] == "unknown"
    assert "نامعلوم" in flags["headline"]


def test_safe_program_is_clear(db) -> None:
    mid = _member('["knee_injury"]')
    program = _program(mid, "bench_press")

    flags = json.loads(program.safety_flags)
    assert flags["status"] == "clear"
    assert flags["safe_to_generate"] is True


def test_safety_flags_always_persist_valid_json(db) -> None:
    """هر برنامه‌ای که ساخته می‌شود باید پرچم قابل‌خواندن داشته باشد."""
    mid = _member("[]")
    program = _program(mid, "row")
    parsed = json.loads(program.safety_flags)
    assert "status" in parsed
    assert "disclaimer_fa" in parsed


def test_malformed_constraints_do_not_crash(db) -> None:
    """اگر ستون constraints خراب باشد، ساخت برنامه نباید بشکند."""
    mid = _member("not-json")
    program = _program(mid, "squat")
    flags = json.loads(program.safety_flags)
    assert flags["status"] == "unknown"

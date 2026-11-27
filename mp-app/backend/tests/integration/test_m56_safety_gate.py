"""Q7 — دروازهٔ ایمنی هنگام ساخت برنامه.

کشف مهم این چرخه: `engine/safety.py` از قبل پروتکل سالمند (D-016) را
داشت؛ بازنویسی کاملش آن را نابود می‌کرد. حالا هر دو دامنه در یک ماژول
زنده‌اند و این تست‌ها رفتار دروازه را در مسیر واقعی ساخت برنامه می‌سنجند.
"""

from __future__ import annotations

import itertools
import json

import pytest
from fastapi.testclient import TestClient

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

    exercise_id = {"squat": 1, "bench_press": 2, "row": 5}.get(movement, 1)
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
                                "exercise_id": exercise_id,
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


def test_unmapped_exercise_needs_review_instead_of_clear(db) -> None:
    from db.base import get_session_factory
    from modules.programs.service import create_program_from_engine_output

    mid = _member('["knee_injury"]')
    with get_session_factory()() as session:
        program = create_program_from_engine_output(
            session,
            mid,
            {
                "goal": "hypertrophy",
                "engine_version": "test",
                "weeks": [
                    {
                        "week_number": 1,
                        "exercises": [
                            {
                                "exercise_id": 999,
                                "day": 1,
                                "sets": 3,
                                "reps": "8-12",
                            }
                        ],
                    }
                ],
            },
        )

    flags = json.loads(program.safety_flags)
    assert flags["status"] == "needs_review"
    assert flags["safe_to_generate"] is False
    assert flags["unmapped_exercises"] == ["999"]


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


# ── MEM-06 — همان پرچم از مسیر عضو هم باید دیده شود، نه فقط از مسیر کارکنان ──
#
# `test_contraindicated_program_is_flagged` فقط ستون دیتابیس را می‌خواند. معیار پذیرش
# MEM-06 دربارهٔ چیزی است که **عضو** می‌بیند؛ اگر مسیر عضو پرچم را حذف یا ساده کند،
# UI مجبور می‌شود حدس بزند و همان نقص قبلی برمی‌گردد. پس اینجا مسیر واقعی
# `GET /api/v1/programs/member/{id}` با توکن خود عضو سنجیده می‌شود.


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.main import create_app
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/safety-api.db")
    reset_engine()
    init_db()
    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()
    reset_engine()


def _member_with_token(constraints: str) -> tuple[dict, int]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"09{n:09d}", full_name=f"m{n}", role="member")
        s.add(user)
        s.commit()
        s.refresh(user)
        member = Member(
            user_id=user.id, gender="male", goal="hypertrophy", constraints=constraints, branch_id=1
        )
        s.add(member)
        s.commit()
        s.refresh(member)
        token = create_access_token(user.id, user.role)
        return {"Authorization": f"Bearer {token}"}, member.id


def _approve(program_id: int) -> None:
    """تأیید مستقیم در دیتابیس: گذار draft→approved در تست‌های خودش سنجیده می‌شود."""
    from datetime import UTC, datetime

    from db.base import get_session_factory
    from db.models import WorkoutProgram

    with get_session_factory()() as s:
        program = s.get(WorkoutProgram, program_id)
        assert program is not None
        program.status = "approved"
        program.approved_at = datetime.now(UTC)
        s.commit()


def test_member_route_returns_the_blocked_verdict(client) -> None:
    """عضو همان «ناسازگار» را می‌بیند که مربی می‌بیند — با جزئیات، نه پرچم خالی."""
    headers, member_id = _member_with_token('["knee_injury"]')
    program = _program(member_id, "squat")
    _approve(program.id)

    response = client.get(f"/api/v1/programs/member/{member_id}", headers=headers)
    assert response.status_code == 200, response.text
    items = response.json()
    assert len(items) == 1

    flags = json.loads(items[0]["safety_flags"])
    assert flags["status"] == "blocked"
    assert flags["safe_to_generate"] is False
    assert flags["blocked"][0]["constraint"] == "knee_injury"
    assert flags["blocked"][0]["label_fa"]
    assert "squat" in flags["blocked"][0]["blocked_exercises"]
    assert flags["blocked"][0]["alternatives"]
    # پرچم باید از همان قاعدهٔ نسخه‌دار بیاید تا UI بتواند نسخه را نشان دهد.
    assert flags["rule_version"]


def test_member_route_does_not_downgrade_unknown_to_clear(client) -> None:
    """غربالگری‌نشده در مسیر عضو هم «نامعلوم» است؛ پاسخ حذف یا سبز نمی‌شود."""
    headers, member_id = _member_with_token("[]")
    program = _program(member_id, "bench_press")
    _approve(program.id)

    response = client.get(f"/api/v1/programs/member/{member_id}", headers=headers)
    assert response.status_code == 200, response.text

    flags = json.loads(response.json()[0]["safety_flags"])
    assert flags["status"] == "unknown"
    assert flags["safe_to_generate"] is False
    assert "نامعلوم" in flags["headline"]

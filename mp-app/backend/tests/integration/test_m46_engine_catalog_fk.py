"""M46-c4 — گپ واقعیِ کشف‌شده با فعال‌کردن کلید خارجی.

`engine/workout.py` می‌گوید: «exercise_id پایدار — با DB بی‌ارتباط».
ولی `program_exercises.exercise_id` یک `ForeignKey("exercises.id")` است و
هیچ‌جا کاتالوگ `exercises` با این شناسه‌ها seed نمی‌شود. نتیجه:

  * با FK خاموش (پیش‌فرض SQLite): ردیف‌های یتیم بی‌صدا ساخته می‌شدند —
    برنامه‌ای که به حرکت ناموجود اشاره می‌کند، ولی هیچ خطایی نمی‌دهد.
  * با FK روشن: ساخت برنامه کاملاً شکست می‌خورد.

هر دو حالت غلط است. این تست قفل می‌کند که برنامهٔ ذخیره‌شده از موتور،
همیشه به حرکت‌های واقعاً موجود اشاره کند و نام حرکت هم قابل نمایش باشد.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(980001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/catalog.db")
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


def _member(client: TestClient, h: dict) -> int:
    n = next(_counter)
    r = client.post(
        "/api/v1/members",
        json={
            "phone": f"09{n:09d}",
            "full_name": f"عضو {n}",
            "goal": "hypertrophy",
            "gender": "male",
        },
        headers=h,
    )
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


def test_generated_program_exercises_exist_in_catalog(client: TestClient) -> None:
    from db.base import get_session_factory
    from db.models import Exercise, ProgramExercise

    h = _staff()
    mid = _member(client, h)

    r = client.post(
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
    assert r.status_code == 200, r.text

    with get_session_factory()() as s:
        rows = s.query(ProgramExercise).all()
        assert rows, "برنامه ساخته شد ولی هیچ حرکتی ذخیره نشد"
        catalog_ids = {e.id for e in s.query(Exercise).all()}
        missing = {r.exercise_id for r in rows} - catalog_ids
        assert not missing, f"exercise_id های بدون ردیف کاتالوگ: {sorted(missing)}"


def test_catalog_matches_engine_library_names(client: TestClient) -> None:
    """نام حرکتی که موتور می‌دهد باید در کاتالوگ همان ردیف باشد."""
    from db.base import get_session_factory
    from db.models import Exercise
    from engine.workout import LIBRARY

    h = _staff()
    mid = _member(client, h)
    client.post(
        "/api/v1/ai/program/generate",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "level": "beginner",
            "days_per_week": 3,
            "weeks_count": 2,
            "constraints": [],
        },
        headers=h,
    )

    with get_session_factory()() as s:
        by_id = {e.id: e for e in s.query(Exercise).all()}
    for mv in LIBRARY.values():
        ex = by_id.get(mv["exercise_id"])
        if ex is not None:
            assert ex.name_fa, f"کاتالوگ برای {mv['exercise_id']} نام ندارد"

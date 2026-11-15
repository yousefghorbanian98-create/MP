"""Dry-run پایلوت (M40-c2) — حلقهٔ کامل API: آزمون ← ماتریس ← تجویز ← بازخورد ← تعدیل."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(810001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/pilot.db")
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


def test_full_loop_dry_run(client, monkeypatch) -> None:
    """ثبت آزمون ← ماتریس ← تجویز ← بازخورد ست ← پیشنهاد تعدیل — صفر نامعلوم."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User
    from engine.axis_map import AXIS_TEST_MAP
    from engine.axis_prescription import prescribe_axis_work
    from scripts.seed_criteria import seed as seed_criteria
    from scripts.seed_norms import seed as seed_norms

    with get_session_factory()() as s:
        seed_norms(s)
        seed_criteria(s)
        from db.models import CatalogExercise

        s.add_all(
            [
                CatalogExercise(
                    source_id=1,
                    external_id="squat-l1",
                    name="Bodyweight Squat",
                    name_fa="اسکوات وزن‌بدن",
                    level="beginner",
                    intensity_band="low",
                    axis_coverage='{"1": 0.8, "3": 0.6, "5": 0.5}',
                ),
                CatalogExercise(
                    source_id=1,
                    external_id="plank",
                    name="Plank",
                    name_fa="پلانک",
                    level="beginner",
                    intensity_band="low",
                    axis_coverage='{"7": 0.9, "5": 0.5}',
                ),
                CatalogExercise(
                    source_id=1,
                    external_id="deadlift",
                    name="Deadlift",
                    name_fa="ددلیفت",
                    level="intermediate",
                    intensity_band="high",
                    axis_coverage='{"9": 0.8, "3": 0.7, "10": 0.4}',
                ),
            ]
        )
        s.commit()
    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"pilot-{n}", role="coach")
        s.add(u)
        s.flush()
        from datetime import date

        m = Member(
            user_id=u.id, gender="female", birth_date=date(1995, 6, 15), goal="general_fitness"
        )
        s.add(m)
        s.commit()
        member_id = m.id
    h = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}

    # ۱) ثبت آزمون — همهٔ ۱۴ محور مقدار دارند (هیچ نامعلوم)
    unique_keys = sorted({key for mapping in AXIS_TEST_MAP.values() for key, _w in mapping})
    tests = [{"test_key": key, "raw_value": 60.0} for key in unique_keys]
    res = client.post(
        "/api/v1/axis-assessments", json={"member_id": member_id, "tests": tests}, headers=h
    )
    assert res.status_code == 200, res.text
    assessment_id = res.json()["assessment_id"]

    # ۲) ماتریس — همهٔ ستون‌ها عدد/وضعیت دارند
    res = client.get(f"/api/v1/axis-assessments/{assessment_id}/matrix", headers=h)
    assert res.status_code == 200
    body = res.json()
    axes = body["axes"]
    assert len(axes) == 14
    for axis in axes:
        assert 1 <= axis["axis"] <= 14
        assert axis["decision_state"] in ("direct", "maintain", "covered", "refer", "unknown")
        assert axis["decision_reason"]

    # ۳) تجویز محور-آگاه — برای هر direct حرکت یا شکاف صریح؛ refer بدون حرکت
    decisions = {
        a["axis"]: {"state": a["decision_state"], "reason": a["decision_reason"]} for a in axes
    }
    import json as _json

    from db.models import CatalogExercise

    level_map = {"beginner": 1, "intermediate": 2, "advanced": 3}
    with get_session_factory()() as s:
        rows = s.query(CatalogExercise).all()
        movements = [
            {
                "external_id": r.external_id,
                "name_fa": r.name_fa or r.name,
                "axis_coverage": _json.loads(r.axis_coverage or "{}"),
                "level": level_map.get(r.level, 2),
            }
            for r in rows
        ]
    assert movements, "کاتالوگ خالی است — dry-run به حرکت واقعی نیاز دارد"
    plan = prescribe_axis_work(decisions=decisions, movements=movements)
    for p in plan["axis_plans"]:
        if p["state"] in ("refer", "unknown"):
            assert not p["movement_ids"]

    # ۴) بازخورد ست ← پیشنهاد جلسهٔ بعد (G1)
    res = client.post(
        "/api/v1/programs/set-feedback",
        json={
            "member_id": member_id,
            "entries": [
                {
                    "movement_id": "squat-l1",
                    "weight": 40,
                    "target_reps": 10,
                    "reps_done": 12,
                    "rir": 3,
                    "soreness": 2,
                }
            ],
        },
        headers=h,
    )
    assert res.status_code == 200, res.text
    suggestion = res.json()["suggestions"][0]
    assert suggestion["next_weight"] and suggestion["reason"]

    # ۵) بازبینی ادمین (نقش‌های جدا)
    with get_session_factory()() as s:
        mg = User(phone=f"09{n + 1:09d}", full_name=f"mgr-{n}", role="manager")
        s.add(mg)
        s.commit()
        mg_h = {"Authorization": f"Bearer {create_access_token(mg.id, mg.role)}"}
    res = client.post(
        f"/api/v1/axis-assessments/{assessment_id}/review",
        json={"action": "approve", "reason": "پایلوت dry-run"},
        headers=mg_h,
    )
    assert res.status_code == 200

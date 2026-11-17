"""تست‌های نردبان‌های پیشرفت (M34-c1)."""

from __future__ import annotations

import json

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.base import Base
from db.models.content import CatalogExercise, ProgressionLadder, ProgressionStep
from scripts.build_progressions import LADDERS, check_names, seed

STEPS_TOTAL = sum(len(ladder.steps) for ladder in LADDERS)


def test_all_ladder_steps_resolve_against_source() -> None:
    resolved = check_names()
    assert len(resolved) == STEPS_TOTAL
    assert len(resolved) == len(set(resolved))  # هر نام فقط یک ردیف


def test_ladders_shape() -> None:
    keys = [ladder.key for ladder in LADDERS]
    assert len(keys) == len(set(keys)) == 10
    for ladder in LADDERS:
        assert all(0.0 <= weight <= 1.0 for weight in ladder.axis_focus.values())
        assert set(ladder.axis_focus) <= {str(i) for i in range(1, 15)}
        assert len(ladder.steps) >= 2
        assert all(step.name_fa for step in ladder.steps)


def test_seed_is_idempotent_and_links_catalog() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    resolved = check_names()
    # فقط ردیف‌های واقعی catalog (idهای حل‌شده) — بدون آن پیوند بی‌معنی است
    for name, external_id in resolved.items():
        session.add(CatalogExercise(external_id=external_id, name=name, source_id=1))
    session.commit()

    first = seed(session, resolved)
    second = seed(session, resolved)
    assert first["ladders"] == 10 and first["steps"] == STEPS_TOTAL
    assert first["linked"] == STEPS_TOTAL
    assert second["linked"] == 0
    assert session.query(ProgressionLadder).count() == 10
    assert session.query(ProgressionStep).count() == STEPS_TOTAL
    linked = session.query(CatalogExercise).filter(CatalogExercise.progression_key != "").count()
    assert linked == STEPS_TOTAL
    session.close()
    engine.dispose()


def test_step_order_strictly_increasing() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    resolved = check_names()
    seed(session, resolved)
    for ladder in LADDERS:
        steps = (
            session.query(ProgressionStep)
            .filter_by(ladder_key=ladder.key)
            .order_by(ProgressionStep.step_no)
            .all()
        )
        assert [s.step_no for s in steps] == list(range(1, len(ladder.steps) + 1))
    session.close()
    engine.dispose()


def test_missing_step_name_fails_loudly(tmp_path) -> None:
    fake = tmp_path / "exercises.json"
    fake.write_text(json.dumps([{"id": "x", "name": "Only One"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="catalog rows missing"):
        check_names(fake)

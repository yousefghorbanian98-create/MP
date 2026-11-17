"""تست‌های ورود کاتالوگ حرکات (M33-c1) — E12: منبع/digest/ایمن ورود."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from db.models.content import CatalogExercise, CatalogSource
from scripts.import_exercise_catalog import (
    DEFAULT_DATA,
    EXPECTED_DIGEST,
    file_digest,
    import_catalog,
    verify_source,
)


def test_vendor_file_present_and_digest_matches() -> None:
    assert DEFAULT_DATA.exists()
    assert file_digest(DEFAULT_DATA) == EXPECTED_DIGEST


def test_verify_source_rejects_tampered(tmp_path: Path) -> None:
    bad = tmp_path / "exercises.json"
    bad.write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError, match="digest mismatch"):
        verify_source(bad)


def test_import_catalog_full_count_and_source_record(session) -> None:
    result = import_catalog(session)
    assert result.inserted == 876
    source = session.query(CatalogSource).filter_by(name="free-exercise-db").one()
    assert source.license == "Unlicense"
    assert source.digest == EXPECTED_DIGEST
    assert source.exercise_count == 876
    assert session.query(CatalogExercise).count() == 876


def test_import_catalog_idempotent(session) -> None:
    first = import_catalog(session)
    second = import_catalog(session)
    assert first.inserted == 876
    assert second.inserted == 0
    assert second.updated == 876
    assert session.query(CatalogExercise).count() == 876
    assert session.query(CatalogSource).count() == 1


def test_import_catalog_row_fields(session) -> None:
    import_catalog(session)
    row = session.query(CatalogExercise).filter(CatalogExercise.name.ilike("%3/4 sit-up%")).one()
    assert row.category == "strength"
    assert row.level == "beginner"
    assert json.loads(row.primary_muscles) == ["abdominals"]
    assert isinstance(json.loads(row.instructions), list)

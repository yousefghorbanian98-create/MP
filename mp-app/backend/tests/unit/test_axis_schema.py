"""تست‌های schema بردار ۱۴محوره (M33-c2)."""

from __future__ import annotations

import json

from db.models.content import CatalogExercise

AXIS_IDS = [str(i) for i in range(1, 15)]


def test_catalog_exercise_axis_fields_default(session) -> None:
    row = CatalogExercise(external_id="t-1", name="Test Move", source_id=1)
    session.add(row)
    session.commit()
    got = session.get(CatalogExercise, row.id)
    assert got.axis_coverage == "{}"
    assert got.intensity_band == ""
    assert got.progression_key == ""


def test_axis_coverage_vector_roundtrip(session) -> None:
    coverage = {axis: 0.0 for axis in AXIS_IDS}
    coverage["3"] = 0.8
    coverage["5"] = 0.5
    row = CatalogExercise(
        external_id="t-2",
        name="Push-Up",
        source_id=1,
        axis_coverage=json.dumps(coverage),
        intensity_band="moderate",
        progression_key="pushup",
    )
    session.add(row)
    session.commit()
    got = session.get(CatalogExercise, row.id)
    loaded = json.loads(got.axis_coverage)
    assert sorted(loaded) == sorted(AXIS_IDS)
    assert loaded["3"] == 0.8
    assert 0.0 <= loaded["5"] <= 1.0
    assert got.progression_key == "pushup"


def test_axis_weights_bounded_validator() -> None:
    # قاعده: وزن‌ها فقط بازهٔ 0..1 — نگهبان helper در ماژول ورود/برچسب‌زنی (M33-c3)
    from scripts.import_exercise_catalog import validate_coverage

    assert validate_coverage({"1": 0.5, "14": 1.0}) is True
    assert validate_coverage({"1": 1.5}) is False
    assert validate_coverage({"0": 0.5}) is False
    assert validate_coverage({"15": 0.5}) is False
    assert validate_coverage({}) is True

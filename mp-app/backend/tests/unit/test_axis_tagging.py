"""تست‌های برچسب‌زنی محوری ۱۴گانه (M33-c3)."""

from __future__ import annotations

import json

from db.models.content import CatalogExercise
from scripts.import_exercise_catalog import validate_coverage
from scripts.tag_axis_coverage import dump_rules, intensity_band, name_fa_for, tag_all, tag_exercise

SQUAT = {
    "name": "Barbell Squat",
    "category": "strength",
    "level": "beginner",
    "force": "push",
    "mechanic": "compound",
    "equipment": "barbell",
    "primary_muscles": ["quadriceps"],
}


def test_tag_exercise_max_merge_and_bounds() -> None:
    coverage, rule_ids = tag_exercise(SQUAT)
    assert "cat-strength" in rule_ids
    assert "mech-compound" in rule_ids
    assert validate_coverage(coverage)
    # max-merge: هیچ محوری جمع نمی‌شود — فقط بیشینه
    assert coverage["3"] == 0.7
    assert coverage["7"] == 0.4


def test_tag_exercise_stretching_hits_mobility() -> None:
    coverage, rule_ids = tag_exercise(
        {"name": "Hamstring Stretch", "category": "stretching", "level": "beginner",
         "force": "static", "mechanic": None, "equipment": "body only", "primary_muscles": ["hamstrings"]}
    )
    assert "cat-stretch" in rule_ids
    assert coverage["1"] == 0.9


def test_registry_covers_all_rules() -> None:
    registry = dump_rules()
    ids = {r["rule_id"] for r in registry}
    assert len(ids) == 23
    assert {"cat-strength", "cat-cardio", "force-static", "muscle-forearm", "equip-foam", "name-breath"} <= ids


def test_name_fa_generation_quality() -> None:
    fa, quality = name_fa_for("Incline Dumbbell Bench Press")
    assert "پرس سینه" in fa
    assert "دمبل" in fa
    assert quality > 0.7
    fa_low, quality_low = name_fa_for("Zzzz Qqqq")
    assert fa_low == ""
    assert quality_low < 0.5


def test_intensity_band_rules() -> None:
    assert intensity_band({**SQUAT}) == "high"  # barbell
    assert intensity_band({"category": "stretching", "level": "intermediate", "equipment": "body only"}) == "low"
    assert intensity_band({"category": "strength", "level": "beginner", "equipment": "body only"}) == "low"


def test_tag_all_on_db(session) -> None:
    session.add(CatalogExercise(external_id="x-1", name="Barbell Squat", source_id=1,
                                category="strength", level="beginner", force="push",
                                mechanic="compound", equipment="barbell",
                                primary_muscles=json.dumps(["quadriceps"])))
    session.add(CatalogExercise(external_id="x-2", name="Bench Press", source_id=1,
                                category="powerlifting", level="intermediate", force="push",
                                mechanic="compound", equipment="barbell",
                                primary_muscles=json.dumps(["chest"])))
    session.commit()
    stats = tag_all(session)
    assert stats == {"rows": 2, "with_axis": 2, "with_fa": 2, "rules_hit": stats["rules_hit"]}
    row = session.query(CatalogExercise).filter_by(external_id="x-1").one()
    coverage = json.loads(row.axis_coverage)
    assert coverage["3"] == 0.7
    assert row.review_status == "candidate"
    meta = json.loads(row.review_meta)
    assert meta["tagger"] == "m33c3-v1"
    assert "cat-strength" in meta["rules"]
    assert row.intensity_band == "high"

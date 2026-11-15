"""G2 — نشانگرهای حجم (MV/MEV/MAV/MRV). نسخهٔ volume-landmarks-1.0."""

from __future__ import annotations

import pytest

from engine.volume import (
    HARD_SET_MAX_RIR,
    VOLUME_VERSION,
    classify_volume,
    count_hard_sets,
    landmarks_for,
    normalize_muscle,
    suggest_weekly_delta,
    summarize_volume,
)


def test_landmarks_are_monotonic() -> None:
    """MV ≤ MEV ≤ MAV_min ≤ MAV_max ≤ MRV — نقض این ترتیب بی‌معناست."""
    for muscle in ("chest", "back", "quads", "hamstrings", "calves", "full_body"):
        for level in ("beginner", "intermediate", "advanced"):
            m = landmarks_for(muscle, level)
            assert m["mv"] <= m["mev"] <= m["mav_min"] <= m["mav_max"] <= m["mrv"], (
                f"{muscle}/{level}: {m}"
            )


def test_landmarks_carry_source() -> None:
    """E07 — هیچ عددی بی‌منبع نمی‌ماند."""
    m = landmarks_for("chest")
    assert "Israetel" in m["source"]
    assert m["rule_version"] == VOLUME_VERSION


def test_advanced_trainees_tolerate_more_than_beginners() -> None:
    b = landmarks_for("chest", "beginner")
    a = landmarks_for("chest", "advanced")
    assert a["mev"] > b["mev"]
    assert a["mrv"] > b["mrv"]


def test_catalog_aliases_map_to_real_groups() -> None:
    """گروه‌های کاتالوگ (legs, posterior_chain…) باید ستون فقرات جدول را پیدا کنند."""
    assert normalize_muscle("legs") == "quads"
    assert normalize_muscle("posterior_chain") == "hamstrings"
    assert normalize_muscle("chest_shoulders") == "chest"
    assert normalize_muscle("back_biceps") == "back"
    assert normalize_muscle("چیز نامعلوم") == "full_body"


@pytest.mark.parametrize(
    ("sets", "expected"),
    [
        (2, "below_mv"),
        (6, "between_mv_mev"),
        (8, "mev"),
        (15, "mav"),
        (20, "above_mav"),
        (30, "mrv_exceeded"),
    ],
)
def test_classification(sets: int, expected: str) -> None:
    assert classify_volume(sets, landmarks_for("chest", "intermediate")) == expected


def test_hard_sets_exclude_easy_sets() -> None:
    """ست با RIR ۵ محرک کافی ندارد — اگر شمرده شود حجم واقعی گم می‌شود."""
    rows = [{"rir": 0}, {"rir": 2}, {"rir": HARD_SET_MAX_RIR}, {"rir": 5}, {"rir": None}]
    c = count_hard_sets(rows)
    assert c["hard"] == 3
    assert c["soft"] == 1
    assert c["unknown"] == 1


def test_unknown_rir_is_not_optimistically_counted() -> None:
    c = count_hard_sets([{"rir": None}, {"rir": None}])
    assert c["hard"] == 0
    assert c["unknown"] == 2


def test_no_feedback_uses_planned_and_says_so() -> None:
    r = summarize_volume(muscle="chest", level="intermediate", planned_sets=12, feedback_rows=[])
    assert r["data_state"] == "no_feedback"
    assert r["effective_sets"] == 12
    assert r["source_of_number"] == "planned"


def test_reported_feedback_uses_hard_sets_not_planned() -> None:
    r = summarize_volume(
        muscle="chest",
        level="intermediate",
        planned_sets=12,
        feedback_rows=[{"rir": 1}, {"rir": 2}],
    )
    assert r["data_state"] == "reported"
    assert r["effective_sets"] == 2
    assert r["source_of_number"] == "reported_hard_sets"
    assert r["status"] == "below_mv"


def test_soreness_overrides_increase() -> None:
    """درد ۸ یعنی بازیابی مقدم بر پیشرفت است، حتی اگر حجم پایین باشد."""
    s = suggest_weekly_delta("below_mv", soreness=8)
    assert s["delta_sets"] < 2
    assert "درد" in s["reason"]


def test_missed_session_freezes_decision() -> None:
    """داده ناقص ⇒ هیچ تغییری. حدس زدن بدترین گزینه است."""
    s = suggest_weekly_delta("mav", missed_sessions=1)
    assert s["delta_sets"] == 0
    assert "ناقص" in s["reason"]


def test_mrv_exceeded_reduces() -> None:
    s = suggest_weekly_delta("mrv_exceeded")
    assert s["delta_sets"] < 0

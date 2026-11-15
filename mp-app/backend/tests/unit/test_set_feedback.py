"""تست‌های بازخورد ست‌به‌ست (M38-c2) — G1: وزن از autoreg، حجم از قواعد درد، بدون LLM."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.set_feedback import SET_FEEDBACK_VERSION, process_set_feedback


def test_progress_weight_via_autoreg() -> None:
    # ۲ تکرار بیشتر از هدف با RIR ۳ (RPE ۷) ← قانون ۲ برای ۲ ← افزایش
    result = process_set_feedback(
        entries=[
            {
                "movement_id": "squat",
                "weight": 60,
                "target_reps": 8,
                "reps_done": 10,
                "rir": 3,
                "soreness": 2,
            },
        ]
    )
    s = result["suggestions"][0]
    assert s["weight_action"] == "increase"
    assert s["next_weight"] == 62.5
    assert s["volume_action"] == "keep"
    assert s["rule_version"] == SET_FEEDBACK_VERSION


def test_high_soreness_triggers_deload() -> None:
    result = process_set_feedback(
        entries=[
            {
                "movement_id": "press",
                "weight": 40,
                "target_reps": 10,
                "reps_done": 10,
                "rir": 1,
                "soreness": 8,
            },
            {
                "movement_id": "press",
                "weight": 40,
                "target_reps": 10,
                "reps_done": 9,
                "rir": 1,
                "soreness": 7,
            },
        ]
    )
    s = result["suggestions"][0]
    assert s["volume_action"] == "deload"
    assert s["next_sets"] == 1  # ۲ ست − ۱
    assert "کاهش یک ست" in s["reason"]


def test_failed_reps_decrease_weight() -> None:
    result = process_set_feedback(
        entries=[
            {
                "movement_id": "row",
                "weight": 50,
                "target_reps": 8,
                "reps_done": 5,
                "rir": 0,
                "soreness": 2,
            },
        ]
    )
    s = result["suggestions"][0]
    assert s["weight_action"] == "decrease"
    assert s["next_weight"] == 45.0


def test_missing_or_invalid_entries_fail_loudly() -> None:
    with pytest.raises(ApiError, match="هیچ ستی"):
        process_set_feedback(entries=[])
    with pytest.raises(ApiError, match="movement_id"):
        process_set_feedback(entries=[{"weight": 40, "target_reps": 8, "reps_done": 8}])
    with pytest.raises(ApiError, match="درد"):
        process_set_feedback(
            entries=[
                {
                    "movement_id": "x",
                    "weight": 40,
                    "target_reps": 8,
                    "reps_done": 8,
                    "soreness": 11,
                },
            ]
        )

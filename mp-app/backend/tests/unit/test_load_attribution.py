"""تست‌های قانون «یک حرکت، چند محور، یک‌بار بار» (M34-c3)."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.axis_rules import LOAD_RULES_VERSION, attribute_load, tally_weekly_load


def test_fatigue_counted_once_multi_axis() -> None:
    # ددلیفت: ۳ محور پوشش داده ولی خستگی فقط ۳ ست — نه ۹
    entry = attribute_load(
        movement_id="deadlift",
        axis_coverage={"3": 0.7, "7": 0.4, "9": 0.8},
        sets=3,
    )
    assert entry["fatigue_units"] == 3
    assert entry["axis_credit"] == {"3": 2.1, "7": 1.2, "9": 2.4}
    assert "یک‌بار" in entry["reason"]
    assert entry["rule_version"] == LOAD_RULES_VERSION


def test_tally_no_double_count_across_axes() -> None:
    e1 = attribute_load(movement_id="squat", axis_coverage={"3": 0.9, "9": 0.5}, sets=4)
    e2 = attribute_load(movement_id="plank", axis_coverage={"7": 0.9, "5": 0.5}, sets=3)
    result = tally_weekly_load([e1, e2])
    # خستگی: ۴ + ۳ = ۷ (مجموعه‌ها یک‌بار) — نه جمع اعتبار محورها
    assert result["total_fatigue"] == 7
    assert result["axis_totals"]["3"] == 3.6
    assert result["axis_totals"]["7"] == 2.7  # فقط پلانک (۰.۹ × ۳)
    assert result["axis_totals"]["5"] == 1.5
    assert result["axis_totals"]["9"] == 2.0
    assert result["movements_counted"] == 2
    assert "هر ست یک‌بار" in result["reason"]


def test_repeat_movement_sessions_sum_fatigue_per_session() -> None:
    e1 = attribute_load(movement_id="press", axis_coverage={"3": 0.7}, sets=3)
    e2 = attribute_load(movement_id="press", axis_coverage={"3": 0.7}, sets=3)
    result = tally_weekly_load([e1, e2])
    assert result["total_fatigue"] == 6
    assert result["axis_totals"]["3"] == 4.2
    assert result["movements_counted"] == 2


def test_missing_coverage_fails_loudly() -> None:
    with pytest.raises(ApiError, match="بردار پوشش ندارد"):
        attribute_load(movement_id="mystery", axis_coverage={}, sets=3)
    with pytest.raises(ApiError, match="نامعتبر"):
        attribute_load(movement_id="x", axis_coverage={"3": 0.5}, sets=-1)


def test_tally_rejects_unknown_entries() -> None:
    with pytest.raises(ApiError, match="هیچ entry"):
        tally_weekly_load([])
    with pytest.raises(ApiError, match="نسخهٔ قاعدهٔ ناشناخته"):
        tally_weekly_load([{"fatigue_units": 3, "axis_credit": {}, "movement_id": "x"}])

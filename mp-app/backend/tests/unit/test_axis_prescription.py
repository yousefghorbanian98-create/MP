"""تست‌های تجویز محور-آگاه (M38-c1) — حالت‌ها، dedup، خستگی یک‌بار، بودجه."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.axis_prescription import DIRECT_SETS, MAINTAIN_SETS, prescribe_axis_work
from engine.axis_rules import decide_axis


def _mov(external_id: str, coverage: dict, level: int = 1) -> dict:
    return {
        "external_id": external_id,
        "name_fa": external_id,
        "axis_coverage": {k: float(v) for k, v in coverage.items()},
        "intensity_band": "moderate",
        "progression_key": "x",
        "level": level,
    }


MOVEMENTS = [
    _mov("pushup-l1", {"3": 0.7, "5": 0.6, "7": 0.4}, level=1),
    _mov("pushup-l3", {"3": 0.8, "5": 0.5, "7": 0.4}, level=3),
    _mov("plank", {"7": 0.9, "5": 0.5}, level=1),
    _mov("deadlift", {"9": 0.8, "3": 0.7, "10": 0.4}, level=2),
    _mov("stretch", {"1": 0.9, "6": 0.4}, level=1),
]


def _decisions(scores: dict[int, float]) -> dict[int, dict]:
    return {axis: decide_axis(axis=axis, score=score) for axis, score in scores.items()}


def test_direct_picks_lowest_level_with_full_sets() -> None:
    result = prescribe_axis_work(
        decisions=_decisions({3: 30}),
        movements=MOVEMENTS,
    )
    direct = result["axis_plans"][0]
    assert direct["state"] == "direct"
    assert direct["movement_ids"] == ["pushup-l1"]  # پایین‌ترین سطح
    assert direct["sets"] == DIRECT_SETS
    assert "دلیل" in direct["reason"] or direct["reason"]


def test_maintain_picks_highest_level_low_dose() -> None:
    result = prescribe_axis_work(decisions=_decisions({3: 85}), movements=MOVEMENTS)
    plan = result["axis_plans"][0]
    assert plan["state"] == "maintain"
    assert plan["movement_ids"] == ["pushup-l3"]
    assert plan["sets"] == MAINTAIN_SETS


def test_covered_uses_carrier_when_nothing_selected() -> None:
    result = prescribe_axis_work(decisions=_decisions({5: 50, 7: 30}), movements=MOVEMENTS)
    by_axis = {p["axis"]: p for p in result["axis_plans"]}
    # محور ۷ direct (30<40) ← plank؛ محور ۵ covered — plank (انتخاب‌شده) پوشش می‌دهد
    assert by_axis[7]["movement_ids"] == ["plank"]
    assert by_axis[5]["movement_ids"] == ["plank"]
    assert by_axis[5]["roles"] == ["covered_in"]


def test_refer_and_unknown_prescribe_nothing() -> None:
    dec = _decisions({4: 30})
    dec[4] = decide_axis(axis=4, score=30, red_flag="درد سینه")
    result = prescribe_axis_work(decisions=dec, movements=MOVEMENTS)
    plan = result["axis_plans"][0]
    assert plan["movement_ids"] == []
    assert "ارجاع" in plan["reason"]


def test_dedup_and_fatigue_counted_once() -> None:
    # deadlift برای محورهای ۳ و ۹ هر دو انتخاب می‌شود ← یک‌بار در بار
    result = prescribe_axis_work(
        decisions=_decisions({3: 30, 9: 30}),
        movements=MOVEMENTS,
    )
    ids = [m["external_id"] for m in result["selected"]]
    assert ids.count("deadlift") == 1  # حرکت‌های یکتا
    assert result["load"]["movements_counted"] == len(result["selected"])
    # خستگی = جمع ست‌ها (ضرب در تعداد محورها نشده)
    assert result["load"]["total_fatigue"] == sum(m["sets"] for m in result["selected"])


def test_fatigue_budget_trims_maintain_first() -> None:
    result = prescribe_axis_work(
        decisions=_decisions({3: 30, 5: 85, 7: 85}),
        movements=MOVEMENTS,
        fatigue_budget=4.0,  # مستقیم ۳ + دو نگهداری ۲+۲ = ۷ ← باید بریده شود
    )
    assert result["load"]["total_fatigue"] <= 4.0
    assert result["trimmed"]


def test_invalid_inputs_fail_loudly() -> None:
    with pytest.raises(ApiError, match="تصمیم"):
        prescribe_axis_work(decisions={}, movements=MOVEMENTS)
    with pytest.raises(ApiError, match="کاتالوگ"):
        prescribe_axis_work(decisions=_decisions({3: 30}), movements=[])
    with pytest.raises(ApiError, match="ناشناخته"):
        prescribe_axis_work(decisions=_decisions({3: 30}), movements=[{"external_id": "x"}])

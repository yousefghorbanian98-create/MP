"""تست‌های قواعد حالت چهارگانه (M34-c2) — مرزها، ارجاع، دلیل‌داری."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.axis_rules import (
    AXIS_RULES_VERSION,
    STATE_COVERED,
    STATE_DIRECT,
    STATE_MAINTAIN,
    STATE_REFER,
    decide_axis,
    decide_program_axes,
)


def test_state_boundaries() -> None:
    assert decide_axis(axis=3, score=0)["state"] == STATE_DIRECT
    assert decide_axis(axis=3, score=39.9)["state"] == STATE_DIRECT
    assert decide_axis(axis=3, score=40)["state"] == STATE_COVERED
    assert decide_axis(axis=3, score=74.9)["state"] == STATE_COVERED
    assert decide_axis(axis=3, score=75)["state"] == STATE_MAINTAIN
    assert decide_axis(axis=3, score=100)["state"] == STATE_MAINTAIN


def test_red_flag_overrides_score() -> None:
    decision = decide_axis(axis=7, score=90, red_flag="درد کمر هنگام خم شدن")
    assert decision["state"] == STATE_REFER
    assert "درد کمر" in decision["reason"]
    assert "پرچم قرمز" in decision["reason"]


def test_out_of_scope_refers() -> None:
    decision = decide_axis(axis=4, score=50, in_scope=False)
    assert decision["state"] == STATE_REFER
    assert "خارج از دامنه" in decision["reason"]


def test_every_decision_carries_reason_and_version() -> None:
    for score in (10, 50, 90):
        decision = decide_axis(axis=1, score=score)
        assert decision["reason"]
        assert decision["rule_version"] == AXIS_RULES_VERSION
        assert str(score) in decision["reason"]


def test_invalid_scores_fail_loudly() -> None:
    with pytest.raises(ApiError, match="نامعلوم"):
        decide_axis(axis=3, score=None)
    with pytest.raises(ApiError, match="بین ۰ و ۱۰۰"):
        decide_axis(axis=3, score=101)
    with pytest.raises(ApiError, match="بین ۰ و ۱۰۰"):
        decide_axis(axis=3, score=-1)
    with pytest.raises(ApiError, match="محور نامعتبر"):
        decide_axis(axis=15, score=50)


def test_program_decisions_all_axes_with_summary() -> None:
    scores = {axis: 20 if axis % 2 else 80 for axis in range(1, 15)}
    result = decide_program_axes(scores, red_flags={4: "درد سینه"}, out_of_scope={12})
    assert len(result["decisions"]) == 14
    states = {d["axis"]: d["state"] for d in result["decisions"]}
    assert states[4] == STATE_REFER
    assert states[12] == STATE_REFER
    assert states[1] == STATE_DIRECT
    assert states[2] == STATE_MAINTAIN
    assert sum(result["summary"].values()) == 14
    assert result["rule_version"] == AXIS_RULES_VERSION


def test_missing_axis_score_fails_loudly() -> None:
    with pytest.raises(ApiError, match="ثبت نشده"):
        decide_program_axes({1: 50})
    with pytest.raises(ApiError, match="هیچ نمره‌ای"):
        decide_program_axes({})

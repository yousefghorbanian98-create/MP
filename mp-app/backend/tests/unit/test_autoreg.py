"""تست‌های قاعدهٔ autoregulation (M29)."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.autoreg import AUTOREG_VERSION, suggest_next_weight


def test_increase_when_over_target_and_easy():
    out = suggest_next_weight(last_weight=50.0, reps_done=12, target_reps=10, rpe=7)
    assert out["action"] == "increase" and out["next_weight"] == 52.5
    assert out["rule_version"] == AUTOREG_VERSION and out["reason"]


def test_decrease_when_under_target():
    out = suggest_next_weight(last_weight=50.0, reps_done=6, target_reps=10, rpe=9)
    assert out["action"] == "decrease" and out["next_weight"] == 45.0


def test_decrease_at_rpe10_even_if_target_met():
    out = suggest_next_weight(last_weight=50.0, reps_done=10, target_reps=10, rpe=10)
    assert out["action"] == "decrease"


def test_maintain_in_band():
    out = suggest_next_weight(last_weight=50.0, reps_done=10, target_reps=10, rpe=8)
    assert out["action"] == "maintain" and out["next_weight"] == 50.0


def test_invalid_inputs_raise_never_fabricate_zero():
    with pytest.raises(ApiError):
        suggest_next_weight(last_weight=0, reps_done=5, target_reps=10)
    with pytest.raises(ApiError):
        suggest_next_weight(last_weight=50, reps_done=5, target_reps=10, rpe=11)

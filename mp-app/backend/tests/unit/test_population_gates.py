"""تست‌های گیت جمعیتی + ورودی پویا + پروتکل سالمند (M25)."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.safety import SENIOR_RULES, apply_senior_protocol
from modules.population.gates import POPULATION_PATHS, assert_generation_allowed
from modules.population.intake import next_questions


def test_only_adult_and_senior_supported() -> None:
    supported = {k for k, v in POPULATION_PATHS.items() if v["status"] == "supported_with_protocol"}
    assert supported == {"adult", "senior_healthy"}


def test_gate_stops_unsupported_explicitly() -> None:
    for path in ("youth", "pregnancy_postpartum", "disability", "elite"):
        with pytest.raises(ApiError) as e:
            assert_generation_allowed(path)
        assert e.value.code == "population_path_gated"
        # نه «برنامهٔ عمومی + هشدار» — توقف صریح با دلیل
        assert "متوقف" in str(e.value)


def test_gate_unknown_path() -> None:
    with pytest.raises(ApiError):
        assert_generation_allowed("martian")


def test_intake_is_goal_dynamic() -> None:
    base = next_questions("hypertrophy")
    ids = {q["id"] for q in base}
    assert {"recent_volume", "priority_muscles"} <= ids
    strength = next_questions("strength")
    assert "target_lifts" in {q["id"] for q in strength}
    # پاسخ‌داده‌شده تکرار نمی‌شود
    more = next_questions("hypertrophy", answered_ids=["age", "experience"])
    assert "age" not in {q["id"] for q in more}
    # محدودیت ← سؤال وضعیت خاص (حداقل‌سازی: فقط اگر محدودیتی باشد)
    with_constraints = next_questions("hypertrophy", constraints=["knee_pain"])
    assert "symptoms" in {q["id"] for q in with_constraints}


def test_senior_protocol_applies_rules() -> None:
    plan = {"days": [{"exercises": [{"name": "press", "weight": 40}]}]}
    out = apply_senior_protocol(plan)
    assert out["days"][0]["exercises"][0]["weight"] == 28.0  # ×0.7
    assert out["safety"]["max_strength_testing"] is False
    assert SENIOR_RULES["stop_criteria"]

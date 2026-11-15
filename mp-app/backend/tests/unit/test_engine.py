"""تست‌های موتور قواعد قطعی (M15) — قطعیت، G8، جایگزینی محدودیت، ریاضی تغذیه."""

from __future__ import annotations

import pytest

from engine.nutrition import bmr_mifflin, generate_nutrition
from engine.workout import RULES, generate_program


def test_determinism_same_input_same_output():
    a = generate_program("hypertrophy", "intermediate", 4, weeks_count=8)
    b = generate_program("hypertrophy", "intermediate", 4, weeks_count=8)
    assert a.to_engine_output() == b.to_engine_output()


def test_numbers_come_only_from_rules_table():
    """گیت G8: اعداد ست/لود/استراحت دقیقاً از جدول قواعد — نه هیچ منبع دیگر."""
    plan = generate_program("strength", "advanced", 3, weeks_count=4)
    rule = RULES[("strength", "advanced")]
    for week in plan.weeks:
        for ex in week.exercises:
            assert ex.sets == rule["sets"]
            assert ex.reps == rule["reps"]
            assert ex.rest_seconds == rule["rest"]
            # progression قطعی: هر ۳ هفته ۵٪ — نه تصادفی/LLM
            expected = min(
                rule["load_pct"] + ((week.week_number - 1) // 3) * 5, rule.get("load_cap", 95)
            )
            assert ex.load_pct == expected


def test_constraint_knee_swaps_back_squat():
    plan = generate_program("hypertrophy", "beginner", 3, weeks_count=2, constraints=["knee"])
    names = [ex.name for week in plan.weeks for ex in week.exercises]
    assert "اسکوات پشت" not in names  # جایگزین شده
    assert "پرس پا" in names


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        generate_program("bulk", "beginner", 3)
    with pytest.raises(ValueError):
        generate_program("hypertrophy", "pro", 3)
    with pytest.raises(ValueError):
        generate_program("hypertrophy", "beginner", 7)


def test_nutrition_math_exact():
    """ریاضی Mifflin-St Jeor قطعی — خروجی دقیق قابل انتظار."""
    assert bmr_mifflin(80, 180, 30, "male") == 10 * 80 + 6.25 * 180 - 5 * 30 + 5  # 1780
    plan = generate_nutrition(80, 180, 30, "male", "moderate", "hypertrophy")
    assert plan.tdee_kcal == round(1780 * 1.55)  # 2759
    assert plan.target_kcal == round(2759 * 1.10)  # 3035
    assert plan.protein_g == round(3035 * 0.30 / 4)
    assert plan.carbs_g == round(3035 * 0.45 / 4)
    assert plan.fat_g == round(3035 * 0.25 / 9)


def test_nutrition_determinism_and_errors():
    a = generate_nutrition(70, 165, 25, "female", "light", "weight_loss")
    b = generate_nutrition(70, 165, 25, "female", "light", "weight_loss")
    assert a.to_dict() == b.to_dict()
    with pytest.raises(ValueError):
        generate_nutrition(70, 165, 25, "female", "light", "bulk")
    with pytest.raises(ValueError):
        generate_nutrition(70, 165, 25, "female", "lazy", "fitness")


def test_explanations_are_text_only():
    """گیت G8: توضیح فقط متن — ساختار خروجی عددی را تغییر نمی‌دهد."""
    from modules.ai_engine.service import explain_nutrition_text, explain_program_text

    e1 = explain_program_text("hypertrophy", "intermediate", 4, 90)
    e2 = explain_nutrition_text("weight_loss", 2200)
    assert isinstance(e1, str) and isinstance(e2, str)
    assert len(e1) > 20 and len(e2) > 20

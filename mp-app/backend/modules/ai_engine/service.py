"""سرویس هوش مصنوعی — موتور قواعد قطعی + توضیح متنی (G8).

قانون G8: همهٔ اعداد (ست/تکرار/لود/کالری/ماکرو) فقط از `engine.*` می‌آیند؛
خروجی LLM فقط در `llm_explanation` متن می‌نشیند و هرگز در اعداد دخیل نیست.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from engine.nutrition import generate_nutrition
from engine.workout import generate_program

TEMPLATE_PROGRAM = (
    "برنامهٔ {goal} برای سطح {level} با {days} روز تمرین در هفته طراحی شده است. "
    "تمرکز هفته‌های نخست بر یادگیری تکنیک و سپس افزایش تدریجی بار است؛ "
    "استراحت بین ست‌ها {rest} ثانیه و پیشرفت بار هر سه هفته اعمال می‌شود."
)

TEMPLATE_NUTRITION = (
    "برنامهٔ غذایی {goal} با هدف {target} کیلوکالری در روز تنظیم شده است. "
    "پروتئین بالا برای حفظ عضله، کربوهیدرات متناسب با تمرین و چربی‌های سالم در اولویت‌اند. "
    "نوشیدن آب کافی و پرهیز از قندهای ساده توصیه می‌شود."
)


def explain_program_text(goal: str, level: str, days: int, rest: int) -> str:
    """توضیح متنی برنامه (G8 — فقط متن)."""
    return TEMPLATE_PROGRAM.format(goal=goal, level=level, days=days, rest=rest)


def explain_nutrition_text(goal: str, target: int) -> str:
    """توضیح متنی تغذیه (G8 — فقط متن)."""
    return TEMPLATE_NUTRITION.format(goal=goal, target=target)


def draft_program_with_explanation(
    db: Session,
    member_id: int,
    goal: str,
    level: str,
    days_per_week: int,
    weeks_count: int = 8,
    constraints: list[str] | None = None,
    coach_id: int | None = None,
):
    """تولید برنامه با موتور قطعی + ثبت draft (G8)."""
    from modules.programs.service import create_program_from_engine_output

    plan = generate_program(goal, level, days_per_week, weeks_count, constraints)
    output = plan.to_engine_output()
    # Safety screening must evaluate the same restrictions used by the engine,
    # including intake values that have not yet been persisted on Member.
    output["constraints"] = list(constraints or [])
    first_rule_rest = (
        plan.weeks[0].exercises[0].rest_seconds if plan.weeks and plan.weeks[0].exercises else 90
    )
    output["llm_explanation"] = explain_program_text(
        goal, level, days_per_week, first_rule_rest
    )  # فقط متن (G8)
    return create_program_from_engine_output(db, member_id, output, coach_id=coach_id)


def draft_nutrition_with_explanation(
    db: Session,
    member_id: int,
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity: str,
    goal: str,
    coach_id: int | None = None,
):
    """تولید برنامهٔ غذایی با موتور قطعی + ثبت draft (G8)."""
    from modules.nutrition.service import create_plan_from_engine

    n = generate_nutrition(weight_kg, height_cm, age, gender, activity, goal)
    output = {
        "daily_kcal": n.target_kcal,
        "protein_g": n.protein_g,
        "carbs_g": n.carbs_g,
        "fat_g": n.fat_g,
        "engine_version": n.engine_version,
        "llm_explanation": explain_nutrition_text(goal, n.target_kcal),  # فقط متن (G8)
        "meals": [],
    }
    return create_plan_from_engine(db, member_id, output, coach_id=coach_id)

"""موتور قواعد قطعی تغذیه (G8) — فرمول‌های ثابت، بدون LLM در اعداد."""

from __future__ import annotations

from dataclasses import dataclass, field

NUTRITION_VERSION = "rules-1.0.0"

# تقسیم ماکرو بر اساس هدف (درصد کالری)
MACRO_SPLITS: dict[str, dict[str, float]] = {
    "hypertrophy": {"protein": 0.30, "carbs": 0.45, "fat": 0.25},
    "strength": {"protein": 0.28, "carbs": 0.47, "fat": 0.25},
    "weight_loss": {"protein": 0.35, "carbs": 0.35, "fat": 0.30},
    "fitness": {"protein": 0.25, "carbs": 0.50, "fat": 0.25},
}

# تعدیل کالری بر اساس هدف (نسبت به TDEE)
CALORIE_ADJUST: dict[str, float] = {
    "hypertrophy": 1.10,  # مازاد ۱۰٪
    "strength": 1.05,
    "weight_loss": 0.85,  # کسری ۱۵٪
    "fitness": 1.0,
}


@dataclass
class NutritionPlan:
    goal: str
    tdee_kcal: int
    target_kcal: int
    protein_g: int
    carbs_g: int
    fat_g: int
    meals_per_day: int
    engine_version: str = NUTRITION_VERSION
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "tdee_kcal": self.tdee_kcal,
            "target_kcal": self.target_kcal,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "meals_per_day": self.meals_per_day,
            "engine_version": self.engine_version,
            "notes": list(self.notes),
        }


def bmr_mifflin(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    """معادلهٔ Mifflin-St Jeor (قطعی)."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if gender == "male" else -161)


def tdee(bmr: float, activity: str) -> float:
    factors = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "athlete": 1.9}
    if activity not in factors:
        raise ValueError(f"سطح فعالیت نامعتبر: {activity}")
    return bmr * factors[activity]


def generate_nutrition(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
    activity: str,
    goal: str,
) -> NutritionPlan:
    """تولید قطعی برنامهٔ غذایی — همان ورودی ← همیشه همان خروجی."""
    if goal not in MACRO_SPLITS:
        raise ValueError(f"هدف نامعتبر: {goal}")
    bmr = bmr_mifflin(weight_kg, height_cm, age, gender)
    t = tdee(bmr, activity)
    target = round(t * CALORIE_ADJUST[goal])
    split = MACRO_SPLITS[goal]
    return NutritionPlan(
        goal=goal,
        tdee_kcal=round(t),
        target_kcal=target,
        protein_g=round(target * split["protein"] / 4),
        carbs_g=round(target * split["carbs"] / 4),
        fat_g=round(target * split["fat"] / 9),
        meals_per_day=3 if goal != "weight_loss" else 4,
        notes=["اعداد فقط از موتور قواعد (G8)", "جایگزینی مواد با نظر تغذیه‌چی"],
    )

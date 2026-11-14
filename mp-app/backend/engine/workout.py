"""موتور قواعد قطعی تمرین (G8) — خروجی ساخت‌یافته، بدون تصادف و بدون LLM در اعداد.

قواعد از مبانی ورزشی ثابت (ACSM-سبک) گرفته شده‌اند — جدول‌ها در همین فایل،
تا هر ورودی یکتا ← خروجی یکتا (deterministic).
"""

from __future__ import annotations

from dataclasses import dataclass, field

ENGINE_VERSION = "rules-1.0.0"

# کتابخانهٔ حرکات (id پایدار — با DB بی‌ارتباط؛ در M16 با جدول exercises مپ می‌شود)
LIBRARY: dict[str, dict] = {
    "back_squat": {
        "exercise_id": 1,
        "name": "اسکوات پشت",
        "pattern": "squat",
        "equipment": "barbell",
    },
    "bench_press": {
        "exercise_id": 2,
        "name": "پرس سینه",
        "pattern": "push",
        "equipment": "barbell",
    },
    "deadlift": {"exercise_id": 3, "name": "ددلیفت", "pattern": "hinge", "equipment": "barbell"},
    "overhead_press": {
        "exercise_id": 4,
        "name": "پرس سرشانه",
        "pattern": "push",
        "equipment": "barbell",
    },
    "barbell_row": {
        "exercise_id": 5,
        "name": "زیربغل هالتر",
        "pattern": "pull",
        "equipment": "barbell",
    },
    "pull_up": {"exercise_id": 6, "name": "بارفیکس", "pattern": "pull", "equipment": "bodyweight"},
    "leg_press": {"exercise_id": 7, "name": "پرس پا", "pattern": "squat", "equipment": "machine"},
    "dumbbell_curl": {
        "exercise_id": 8,
        "name": "جلوبازو دمبل",
        "pattern": "pull",
        "equipment": "dumbbell",
    },
    "triceps_pushdown": {
        "exercise_id": 9,
        "name": "پشت‌بازو کابل",
        "pattern": "push",
        "equipment": "cable",
    },
    "plank": {"exercise_id": 10, "name": "پلانک", "pattern": "core", "equipment": "bodyweight"},
    "lunge": {"exercise_id": 11, "name": "لانج", "pattern": "squat", "equipment": "dumbbell"},
    "lat_pulldown": {
        "exercise_id": 12,
        "name": "زیربغل سیم‌کش",
        "pattern": "pull",
        "equipment": "machine",
    },
    "leg_curl": {
        "exercise_id": 13,
        "name": "پشت‌ران پا",
        "pattern": "hinge",
        "equipment": "machine",
    },
    "face_pull": {"exercise_id": 14, "name": "فیس‌پول", "pattern": "pull", "equipment": "cable"},
    "hip_thrust": {
        "exercise_id": 15,
        "name": "هیپ‌ترست",
        "pattern": "hinge",
        "equipment": "barbell",
    },
    "calf_raise": {"exercise_id": 16, "name": "ساق پا", "pattern": "squat", "equipment": "machine"},
}

# جدول قواعد: هدف × سطح → (ست، تکرار، درصد ۱RM، استراحت)
RULES: dict[tuple[str, str], dict] = {
    ("hypertrophy", "beginner"): {"sets": 3, "reps": "10-12", "load_pct": 65, "rest": 90},
    ("hypertrophy", "intermediate"): {"sets": 4, "reps": "8-12", "load_pct": 70, "rest": 90},
    ("hypertrophy", "advanced"): {"sets": 4, "reps": "6-12", "load_pct": 75, "rest": 120},
    ("strength", "beginner"): {"sets": 3, "reps": "5", "load_pct": 70, "rest": 120},
    ("strength", "intermediate"): {"sets": 4, "reps": "5", "load_pct": 77, "rest": 150},
    ("strength", "advanced"): {"sets": 5, "reps": "3", "load_pct": 85, "rest": 180},
    ("weight_loss", "beginner"): {"sets": 2, "reps": "12-15", "load_pct": 55, "rest": 60},
    ("weight_loss", "intermediate"): {"sets": 3, "reps": "12-15", "load_pct": 60, "rest": 60},
    ("weight_loss", "advanced"): {"sets": 3, "reps": "10-15", "load_pct": 65, "rest": 60},
    ("fitness", "beginner"): {"sets": 2, "reps": "12", "load_pct": 55, "rest": 60},
    ("fitness", "intermediate"): {"sets": 3, "reps": "12", "load_pct": 60, "rest": 75},
    ("fitness", "advanced"): {"sets": 3, "reps": "10-12", "load_pct": 65, "rest": 75},
}

SPLITS: dict[int, list[str]] = {
    3: ["push", "pull", "legs"],
    4: ["push", "pull", "legs", "full"],
    5: ["push", "pull", "legs", "upper", "lower"],
    6: ["push", "pull", "legs", "push", "pull", "legs"],
}

DAY_MOVES: dict[str, list[str]] = {
    "push": ["bench_press", "overhead_press", "triceps_pushdown", "plank"],
    "pull": ["deadlift", "barbell_row", "pull_up", "dumbbell_curl"],
    "legs": ["back_squat", "leg_press", "leg_curl", "calf_raise"],
    "full": ["back_squat", "bench_press", "barbell_row", "plank"],
    "upper": ["bench_press", "barbell_row", "overhead_press", "lat_pulldown"],
    "lower": ["back_squat", "leg_curl", "hip_thrust", "calf_raise"],
}

# محدودیت‌ها: حرکات ممنوعه به‌ازای هر آسیب (تعویض قطعی)
CONSTRAINT_SWAPS: dict[str, dict[str, str]] = {
    "knee": {"back_squat": "leg_press", "lunge": "leg_press"},
    "shoulder": {"overhead_press": "face_pull", "bench_press": "lat_pulldown"},
    "lower_back": {"deadlift": "leg_curl", "back_squat": "leg_press"},
    "wrist": {"bench_press": "push_up_placeholder", "barbell_row": "lat_pulldown"},
}


@dataclass
class ExerciseSlot:
    exercise_id: int
    name: str
    day: int
    order: int
    sets: int
    reps: str
    load_pct: int
    rest_seconds: int
    notes: str = ""


@dataclass
class WeekPlan:
    week_number: int
    focus: str
    exercises: list[ExerciseSlot] = field(default_factory=list)


@dataclass
class ProgramPlan:
    goal: str
    engine_version: str
    weeks: list[WeekPlan] = field(default_factory=list)
    numbers_source: str = "rules_table"  # G8: اعداد فقط از این موتور

    def to_engine_output(self) -> dict:
        """خروجی سازگار با `create_program_from_engine_output`."""
        return {
            "goal": self.goal,
            "engine_version": self.engine_version,
            "llm_explanation": "",  # جداگانه پر می‌شود — فقط متن (G8)
            "weeks": [
                {
                    "week_number": w.week_number,
                    "focus": w.focus,
                    "exercises": [vars(e) for e in w.exercises],
                }
                for w in self.weeks
            ],
        }


def generate_program(
    goal: str,
    level: str,
    days_per_week: int,
    weeks_count: int = 8,
    constraints: list[str] | None = None,
) -> ProgramPlan:
    """تولید قطعی برنامه — همان ورودی ← همیشه همان خروجی."""
    if goal not in ("hypertrophy", "strength", "weight_loss", "fitness"):
        raise ValueError(f"هدف نامعتبر: {goal}")
    if level not in ("beginner", "intermediate", "advanced"):
        raise ValueError(f"سطح نامعتبر: {level}")
    if days_per_week not in SPLITS:
        raise ValueError(f"تعداد روز باید ۳ تا ۶ باشد: {days_per_week}")

    rule = RULES[(goal, level)]
    split = SPLITS[days_per_week]
    constraints = constraints or []
    plan = ProgramPlan(goal=goal, engine_version=ENGINE_VERSION)

    for wk in range(1, weeks_count + 1):
        # progression قطعی: هر ۳ هفته ۵٪ به لود اضافه می‌شود (نه LLM)
        wave = (wk - 1) // 3
        load_pct = min(rule["load_pct"] + wave * 5, 95)
        week = WeekPlan(week_number=wk, focus=goal)
        day_index = (wk - 1) % days_per_week  # شروع روز در گردش هفتگی
        for d in range(days_per_week):
            day_kind = split[(day_index + d) % days_per_week]
            for order, key in enumerate(DAY_MOVES[day_kind]):
                use_key = key
                note = ""
                for c in constraints:
                    swapped = CONSTRAINT_SWAPS.get(c, {}).get(key)
                    if swapped and swapped in LIBRARY:
                        use_key = swapped
                        note = f"جایگزین به‌خاطر محدودیت {c}"
                move = LIBRARY[use_key]
                week.exercises.append(
                    ExerciseSlot(
                        exercise_id=move["exercise_id"],
                        name=move["name"],
                        day=d + 1,
                        order=order,
                        sets=rule["sets"],
                        reps=rule["reps"],
                        load_pct=load_pct,
                        rest_seconds=rule["rest"],
                        notes=note,
                    )
                )
        plan.weeks.append(week)
    return plan

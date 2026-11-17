"""همگام‌سازی کاتالوگ `exercises` با کتابخانهٔ موتور (M46-c4).

مسئله‌ای که این ماژول حل می‌کند
------------------------------
`engine/workout.py` می‌گوید `exercise_id` «پایدار و بی‌ارتباط با DB» است،
ولی `program_exercises.exercise_id` یک `ForeignKey("exercises.id")` دارد.
هیچ migration یا seedی کاتالوگ را پر نمی‌کرد. نتیجه:

  * SQLite با FK خاموش → ردیف یتیم، بدون هیچ خطایی (بدترین حالت: خرابیِ خاموش)
  * FK روشن → ساخت برنامه کاملاً 500 می‌شد

راه‌حل: پیش از نوشتن برنامه، ردیف‌های ارجاع‌شده را idempotent بساز.
این «seed جادویی مخفی» نیست: قطعی است، از همان LIBRARY می‌آید و
تکرارش هیچ اثری ندارد.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine.workout import LIBRARY

# نقشهٔ pattern موتور ← گروه عضلانی نمایشی کاتالوگ
_PATTERN_TO_MUSCLE: dict[str, str] = {
    "squat": "legs",
    "hinge": "posterior_chain",
    "push": "chest_shoulders",
    "pull": "back_biceps",
    "core": "core",
}


def _muscle_for(pattern: str) -> str:
    return _PATTERN_TO_MUSCLE.get(pattern, "full_body")


def ensure_exercises(db: Session, exercise_ids: set[int]) -> int:
    """اطمینان از وجود ردیف کاتالوگ برای هر شناسه — بازگشت تعداد ردیف‌های ساخته‌شده.

    idempotent: اگر ردیف باشد، دست نمی‌خورد.
    """
    from db.models import Exercise

    if not exercise_ids:
        return 0

    existing = set(
        db.scalars(select(Exercise.id).where(Exercise.id.in_(sorted(exercise_ids)))).all()
    )
    missing = sorted(set(exercise_ids) - existing)
    if not missing:
        return 0

    by_id = {mv["exercise_id"]: (key, mv) for key, mv in LIBRARY.items()}
    created = 0
    for ex_id in missing:
        key, mv = by_id.get(
            ex_id,
            (
                f"unknown_{ex_id}",
                {"name": f"حرکت {ex_id}", "pattern": "full_body", "equipment": ""},
            ),
        )
        db.add(
            Exercise(
                id=ex_id,
                external_id=key,
                name_fa=mv["name"],
                name_en=key.replace("_", " "),
                muscle_group=_muscle_for(mv.get("pattern", "")),
                equipment=mv.get("equipment", ""),
            )
        )
        created += 1
    db.flush()
    return created

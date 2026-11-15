"""اعمال پیشنهاد بازخورد ست روی هفتهٔ بعد — G1 کامل (M48-c1).

پیش از این فایل، حلقهٔ G1 نیمه‌کاره بود:
`POST /programs/set-feedback` بازخورد را ذخیره می‌کرد و یک پیشنهاد
برمی‌گرداند، ولی هیچ ردیفی در برنامه تغییر نمی‌کرد. یعنی مربی باید
پیشنهاد را می‌خواند و دستی اعمال می‌کرد — که در عمل هرگز نمی‌شد.

قواعد (همه قطعی، بدون LLM در اعداد — G8):
  * فقط از هفتهٔ ۲ به بعد؛ هفتهٔ ۱ گذشته است و بازنویسی‌اش جعل تاریخ است.
  * فقط همان برنامهٔ گزارش‌شده؛ اگر program_id خالی باشد، آخرین برنامهٔ عضو.
  * حرکت ناشناخته ⇒ گزارش، نه خطا و نه سکوت.
  * ست‌ها هرگز صفر نمی‌شوند (کف = ۱).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from engine.workout import LIBRARY

FEEDBACK_APPLY_VERSION = "feedback-apply-1.0"

MIN_SETS = 1
MAX_LOAD_PCT = 100
LOAD_STEP_PCT = 5  # هر پلهٔ پیشنهاد وزنی ≈ ۵٪ بار نسبی


def _exercise_ids_by_key() -> dict[str, int]:
    """کلید LIBRARY (`back_squat`) ← شناسهٔ عددی کاتالوگ."""
    return {key: mv["exercise_id"] for key, mv in LIBRARY.items()}


def _exercise_ids_by_name() -> dict[str, int]:
    """نام فارسی ← شناسه، تا حرکت را با اسم هم بتوان اشاره کرد."""
    return {mv["name"]: mv["exercise_id"] for mv in LIBRARY.values()}


def resolve_exercise_id(movement_id: str) -> int | None:
    """movement_id می‌تواند کلید LIBRARY، نام فارسی، یا خودِ شناسهٔ عددی باشد."""
    key = str(movement_id).strip()
    by_key = _exercise_ids_by_key()
    if key in by_key:
        return by_key[key]
    by_name = _exercise_ids_by_name()
    if key in by_name:
        return by_name[key]
    if key.isdigit():
        ex_id = int(key)
        return ex_id if ex_id in {v["exercise_id"] for v in LIBRARY.values()} else None
    return None


def apply_suggestions(
    db: Session,
    *,
    program,
    suggestions: list[dict],
    from_week: int = 2,
) -> dict:
    """اعمال پیشنهادها روی همهٔ هفته‌های ≥ `from_week` برنامهٔ داده‌شده.

    خروجی همیشه گزارش می‌دهد چه اتفاقی افتاد — حتی وقتی هیچ ردیفی نبود.
    """
    from db.models import ProgramExercise, ProgramWeek

    matched: list[dict] = []
    unmatched: list[str] = []
    rows_changed = 0
    weeks_touched: set[int] = set()

    if program is None:
        return {
            "weeks_updated": 0,
            "rows_changed": 0,
            "matched": [],
            "unmatched_movements": [
                s.get("movement_id") for s in suggestions if s.get("movement_id")
            ],
            "reason": "برنامه‌ای برای اعمال بازخورد یافت نشد",
            "rule_version": FEEDBACK_APPLY_VERSION,
        }

    weeks = list(
        db.scalars(
            select(ProgramWeek)
            .where(ProgramWeek.program_id == program.id, ProgramWeek.week_number >= from_week)
            .order_by(ProgramWeek.week_number)
        )
    )
    week_ids = [w.id for w in weeks]

    for sugg in suggestions:
        movement_id = sugg.get("movement_id")
        if not movement_id:
            continue
        ex_id = resolve_exercise_id(movement_id)
        if ex_id is None:
            unmatched.append(str(movement_id))
            continue

        rows = []
        if week_ids:
            rows = list(
                db.scalars(
                    select(ProgramExercise).where(
                        ProgramExercise.week_id.in_(week_ids),
                        ProgramExercise.exercise_id == ex_id,
                    )
                )
            )
        if not rows:
            # حرکت معتبر است ولی در این برنامه نیست (مثلاً برنامهٔ دیگری)
            unmatched.append(str(movement_id))
            continue

        volume_action = sugg.get("volume_action")
        weight_action = sugg.get("weight_action")
        changed_here = 0
        for row in rows:
            before = (row.sets, row.load_pct)
            # حجم نسبت به ست‌های *برنامه* تعدیل می‌شود، نه نسبت به تعداد گزارش.
            # `next_sets` موتور از تعداد ردیف‌های ارسالی می‌آید و اگر عضو فقط
            # یک ست گزارش کند، برنامهٔ ۳ ستی را به ۱ ست سقوط می‌داد.
            if volume_action == "deload":
                row.sets = max(MIN_SETS, (row.sets or MIN_SETS) - 1)
            elif sugg.get("next_sets") is not None and volume_action == "keep":
                row.sets = max(MIN_SETS, int(sugg["next_sets"]))
            if weight_action in ("increase", "increase_load", "up"):
                row.load_pct = min(MAX_LOAD_PCT, (row.load_pct or 0) + LOAD_STEP_PCT)
            elif weight_action in ("decrease", "decrease_load", "down"):
                row.load_pct = max(1, (row.load_pct or 0) - LOAD_STEP_PCT)
            if (row.sets, row.load_pct) != before:
                changed_here += 1
                weeks_touched.add(row.week_id)
        if changed_here:
            rows_changed += changed_here
            matched.append(
                {
                    "movement_id": movement_id,
                    "exercise_id": ex_id,
                    "rows": changed_here,
                }
            )
        else:
            # حرکت پیدا شد ولی چیزی عوض نشد (مثلاً keep با همان ست‌ها)
            matched.append({"movement_id": movement_id, "exercise_id": ex_id, "rows": 0})

    db.commit()

    return {
        "weeks_updated": len(weeks_touched),
        "rows_changed": rows_changed,
        "matched": matched,
        "unmatched_movements": unmatched,
        "reason": (
            f"{rows_changed} ردیف در {len(weeks_touched)} هفته به‌روز شد؛ "
            f"از هفتهٔ {from_week} به بعد (هفتهٔ گذشته دست‌نخورده می‌ماند)"
        ),
        "rule_version": FEEDBACK_APPLY_VERSION,
    }

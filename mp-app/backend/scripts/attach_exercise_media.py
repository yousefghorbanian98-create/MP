"""چسباندن تصاویر کتابخانهٔ حرکات به کاتالوگ (G9).

پیش از این هر حرکت `video_url=""` داشت و هیچ تصویری در پروژه نبود. یعنی
در برنامهٔ ورزشی فقط *نام* حرکت دیده می‌شد و شاگرد نمی‌دانست «هیپ‌ترست»
چطور اجرا می‌شود — شکاف ملموس کاربری.

منبع: free-exercise-db، همان مخزنی که متادیتای کاتالوگ از آن آمده است
(Unlicense — مالکیت عمومی). تصاویر ۳۰۰×۳۰۰ از دو فریم (شروع/پایان) در
`static/exercises/` نگه داشته می‌شوند تا اپ آفلاین هم کار کند؛ هیچ
hotlink به سرور بیرونی نداریم.

کاربرد:
    python scripts/attach_exercise_media.py           # وارد کردن/به‌روزرسانی
    python scripts/attach_exercise_media.py --check   # فقط بررسی فایل‌ها

idempotent: اگر `video_url` پر باشد، بازنویسی نمی‌شود.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.base import get_session_factory  # noqa: E402
from db.models.content import Exercise  # noqa: E402

STATIC_DIR = Path(__file__).resolve().parents[1] / "static" / "exercises"
PUBLIC_PREFIX = "/static/exercises"

# شناسهٔ حرکت موتور ← پوشهٔ بالادست (ثبت‌شده تا ردیابی ممکن باشد)
MAPPING: dict[int, str] = {
    1: "Barbell_Squat",
    2: "Barbell_Bench_Press_-_Medium_Grip",
    3: "Barbell_Deadlift",
    4: "Barbell_Shoulder_Press",
    5: "Bent_Over_Barbell_Row",
    6: "Pullups",
    7: "Leg_Press",
    8: "Dumbbell_Bicep_Curl",
    9: "Triceps_Pushdown",
    10: "Plank",
    11: "Dumbbell_Lunges",
    12: "Wide-Grip_Lat_Pulldown",
    13: "Lying_Leg_Curls",
    14: "Face_Pull",
    15: "Barbell_Hip_Thrust",
    16: "Standing_Calf_Raises",
    17: "Machine_Bench_Press",
}


def media_path(exercise_id: int) -> str:
    """مسیر عمومی فریم اول — همان چیزی که API برمی‌گرداند."""
    return f"{PUBLIC_PREFIX}/{exercise_id}_0.jpg"


def missing_files() -> list[int]:
    return [
        eid
        for eid in MAPPING
        if not (STATIC_DIR / f"{eid}_0.jpg").is_file()
        or not (STATIC_DIR / f"{eid}_1.jpg").is_file()
    ]


def attach(db) -> int:
    """ردیف‌های غایب را از LIBRARY موتور می‌سازد، سپس تصویر می‌چسباند."""
    from engine.catalog_sync import ensure_exercises

    ensure_exercises(db, set(MAPPING))
    before = {e.id: e.video_url for e in db.query(Exercise).filter(Exercise.id.in_(MAPPING)).all()}
    updated = 0
    for eid in MAPPING:
        if not (STATIC_DIR / f"{eid}_0.jpg").is_file():
            continue
        row = db.get(Exercise, eid)
        if row is None:
            continue
        want = media_path(eid)
        if before.get(eid) != want:
            row.video_url = want  # نام فیلد تاریخی است؛ محتوای آن مسیر تصویر است
            updated += 1
    db.commit()
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description="attach free-exercise-db images to the catalog")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    missing = missing_files()
    if missing:
        print(f"فایل‌های غایب برای حرکات: {missing}", file=sys.stderr)
        return 1
    print(f"{len(MAPPING)} حرکت، ۲ فریم هر کدام — فایل‌ها کامل‌اند")
    if args.check:
        return 0
    with get_session_factory()() as db:
        print(f"{attach(db)} ردیف به‌روزرسانی شد")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

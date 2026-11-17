"""روتر library — کتابخانهٔ حرکات با تصویر (G9).

پیش از این، `Exercise.video_url` همیشه خالی بود و هیچ مسیر API برای
دیدن حرکات وجود نداشت: در برنامهٔ ورزشی فقط نام حرکت دیده می‌شد و
شاگرد نمی‌دانست «هیپ‌ترست» چطور اجرا می‌شود.

تصاویر از free-exercise-db (Unlicense / مالکیت عمومی) گرفته شده‌اند و
از خودِ همین اپ در `/static/exercises/…` سرو می‌شوند — نه hotlink به
سرور بیرونی، تا PWA آفلاین هم تصویر داشته باشد.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import CurrentUser, DbSession, require_permission
from app.errors import NotFoundError

router = APIRouter(
    prefix="/library", tags=["library"], dependencies=[Depends(require_permission())]
)


class ExerciseMediaOut(BaseModel):
    exercise_id: int
    name_fa: str
    name_en: str
    muscle_group: str
    equipment: str
    difficulty: str
    instructions_fa: str = ""
    image_url: str = ""
    image_url_alt: str = ""
    # M60/R6 — انیمیشن اجرای حرکت (GIF ساخته‌شده از دو فریم شروع/پایان).
    # خالی یعنی برای این حرکت انیمیشن ساخته نشده؛ مصرف‌کننده باید به
    # `image_url` برگردد، نه اینکه تصویر شکسته نشان دهد.
    gif_url: str = ""


@router.get(
    "/exercises",
    response_model=list[ExerciseMediaOut],
    summary="کتابخانهٔ حرکات با تصویر اجرا (G9)",
)
def list_exercises(
    db: DbSession,
    user: CurrentUser,
    muscle_group: str | None = Query(None, max_length=40),
    q: str | None = Query(None, max_length=60),
    limit: int = Query(100, ge=1, le=300),
):
    from sqlalchemy import or_, select

    from db.models import Exercise

    stmt = select(Exercise).order_by(Exercise.id)
    if muscle_group:
        stmt = stmt.where(Exercise.muscle_group == muscle_group)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Exercise.name_fa.like(like), Exercise.name_en.like(like)))
    rows = db.scalars(stmt.limit(limit)).all()

    out: list[ExerciseMediaOut] = []
    for ex in rows:
        first = ex.video_url or ""
        alt = first.replace("_0.jpg", "_1.jpg") if first.endswith("_0.jpg") else ""
        out.append(
            ExerciseMediaOut(
                exercise_id=ex.id,
                name_fa=ex.name_fa,
                name_en=ex.name_en,
                muscle_group=ex.muscle_group,
                equipment=ex.equipment,
                difficulty=ex.difficulty,
                instructions_fa=ex.instructions_fa,
                image_url=first,
                image_url_alt=alt,
                gif_url=_gif_for(first),
            )
        )
    return out


def _gif_for(image_url: str) -> str:
    """مسیر GIF متناظر با تصویر — فقط اگر فایل واقعاً موجود باشد.

    عمداً وجود فایل روی دیسک بررسی می‌شود: اگر GIF ساخته نشده باشد مسیر
    برنمی‌گردانیم، تا کلاینت تصویر شکسته دریافت نکند. (نسخهٔ اول این بررسی
    را نداشت و برای حرکات بدون GIF یک ۴۰۴ برمی‌گرداند.)
    """
    if not image_url.endswith("_0.jpg"):
        return ""
    candidate = image_url[: -len("_0.jpg")] + ".gif"
    name = candidate.rsplit("/", 1)[-1]
    if (Path(__file__).resolve().parents[2] / "static" / "exercises" / name).is_file():
        return candidate
    return ""


@router.get(
    "/exercises/{exercise_id}",
    response_model=ExerciseMediaOut,
    summary="یک حرکت با تصویر و توضیح",
)
def get_exercise(exercise_id: int, db: DbSession, user: CurrentUser):
    from db.models import Exercise

    ex = db.get(Exercise, exercise_id)
    if ex is None:
        raise NotFoundError("این حرکت در کتابخانه نیست")
    first = ex.video_url or ""
    alt = first.replace("_0.jpg", "_1.jpg") if first.endswith("_0.jpg") else ""
    return ExerciseMediaOut(
        exercise_id=ex.id,
        name_fa=ex.name_fa,
        name_en=ex.name_en,
        muscle_group=ex.muscle_group,
        equipment=ex.equipment,
        difficulty=ex.difficulty,
        instructions_fa=ex.instructions_fa,
        image_url=first,
        image_url_alt=alt,
        gif_url=_gif_for(first),
    )

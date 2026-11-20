"""روتر گزارش زمان‌بندی‌شده (QF-23) — خواندن و اجرای دستی.

مسیر زیر `/finance/reports` است تا از DENIES موجود برای `/reports/*`
(گزارش محرمانهٔ سلامت) جدا بماند: هزینه/درآمد باشگاه و گزارش سلامت عضو دو
دامنهٔ متفاوت‌اند و نباید یک قاعدهٔ دسترسی بگیرند.
"""

from __future__ import annotations

from datetime import UTC, date

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, DbSession, require_permission
from app.errors import ApiError
from app.security.grants import require_grant
from modules.reports import schedule

router = APIRouter(
    prefix="/finance/reports",
    tags=["reports"],
    dependencies=[Depends(require_permission())],
)


@router.get(
    "/schedule",
    summary="وضعیت گزارش‌های زمان‌بندی‌شده (QF-23)",
    dependencies=[Depends(require_grant("finance.read"))],
)
def schedule_status(db: DbSession, user: CurrentUser):
    return schedule.status(db)


@router.post(
    "/schedule/{job_key}/run",
    summary="اجرای دستی یک گزارش زمان‌بندی‌شده (QF-23)",
    dependencies=[Depends(require_grant("finance.write"))],
)
def run_job(job_key: str, db: DbSession, user: CurrentUser):
    return schedule.run_job(db, job_key)


@router.get(
    "/daily/{run_date}",
    summary="گزارش مالی روزانهٔ ثبت‌شده (QF-23)",
    dependencies=[Depends(require_grant("finance.read"))],
)
def daily(run_date: str, db: DbSession, user: CurrentUser):
    try:
        day = date.fromisoformat(run_date)
    except ValueError as exc:
        raise ApiError("تاریخ باید به شکل YYYY-MM-DD باشد", code="invalid_date") from exc
    return schedule.daily_report(db, day)


@router.get(
    "/period",
    summary="گزارش سود/زیان دوره‌ای با بازگشت‌ها — هفته/ماه/سال جلالی تهران (QF-10)",
    dependencies=[Depends(require_grant("finance.read"))],
)
def period(
    db: DbSession,
    user: CurrentUser,
    kind: str = "month",
    anchor: str | None = None,
):
    from datetime import datetime as _dt

    from modules.reports import period as period_mod

    if anchor is None:
        day = schedule.tehran_date(_dt.now(UTC))
    else:
        try:
            day = date.fromisoformat(anchor)
        except ValueError as exc:
            raise ApiError("تاریخ باید به شکل YYYY-MM-DD باشد", code="invalid_date") from exc
    return period_mod.period_report(db, kind, day)

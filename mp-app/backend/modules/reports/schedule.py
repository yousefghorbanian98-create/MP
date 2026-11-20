"""گزارش مالی روزانه — تک‌فعال در هر روزِ تهران (QF-23).

# چرا «روز تهران» و نه UTC

مالک گزارش «دیروز» را به وقت تهران می‌خواند. اگر مرز روز UTC باشد، اجرای
۰۰:۳۰ تهران (= ۲۱:۰۰ UTC دیروز) گزارش را در سبد روز قبل می‌اندازد و عددها با
تصور مالک یکی نیست. پس سبد روز از `Asia/Tehran` ساخته می‌شود و مبلغ‌ها از همان
بازهٔ UTC معادل جمع می‌شوند.

# چرا idempotency روی دیتابیس

ری‌استارت scheduler، اجرای دستی دوباره و دو worker هم‌زمان سه راه تولید گزارش
تکراری‌اند. کلید یکتای `(job_key, run_date)` تضمین می‌کند دومی «همان ردیف» را
برگرداند، نه ردیف تازه.

# چرا عدد در اعلان نیست

مبلغ درآمد را هر کسی که به لاگ/اعلان دسترسی دارد نباید ببیند. اعلان فقط
می‌گوید «گزارش آماده است»؛ عددها از endpoint با `finance.read` می‌آیند.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiError
from db.models import Expense, Payment, ReportRun
from modules.admin.service import audit

TEHRAN = ZoneInfo("Asia/Tehran")
JOBS: dict[str, str] = {"daily_finance": "گزارش مالی روزانهٔ باشگاه"}


def tehran_date(now: datetime) -> date:
    """تاریخ محلی تهران برای یک لحظهٔ UTC-aware."""
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    return now.astimezone(TEHRAN).date()


def _day_window(day: date) -> tuple[datetime, datetime]:
    """مرزهای UTC همان روز تهران: [شروع، پایان)."""
    start_local = datetime.combine(day, time(0, 0), tzinfo=TEHRAN)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def totals(db: Session, day: date) -> dict:
    """جمع پرداخت‌های موفق و هزینه‌های ثبت‌شدهٔ همان روز تهران."""
    start_utc, end_utc = _day_window(day)
    paid_sum, paid_count = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0), func.count(Payment.id)).where(
            Payment.status == "paid",
            Payment.paid_at.is_not(None),
            Payment.paid_at >= start_utc,
            Payment.paid_at < end_utc,
        )
    ).one()
    exp_sum, exp_count = db.execute(
        select(func.coalesce(func.sum(Expense.amount_rial), 0), func.count(Expense.id)).where(
            Expense.deleted_at.is_(None),
            Expense.spent_on == day,
        )
    ).one()
    payments_total = int(paid_sum or 0)
    expenses_total = int(exp_sum or 0)
    return {
        "run_date": day.isoformat(),
        "payments_total_rial": payments_total,
        "expenses_total_rial": expenses_total,
        "net_rial": payments_total - expenses_total,
        "payments_count": int(paid_count or 0),
        "expenses_count": int(exp_count or 0),
    }


def _existing(db: Session, job_key: str, day: date) -> ReportRun | None:
    return db.scalar(
        select(ReportRun).where(ReportRun.job_key == job_key, ReportRun.run_date == day)
    )


def _serialize(row: ReportRun, *, created: bool) -> dict:
    return {
        "job_key": row.job_key,
        "run_date": row.run_date.isoformat(),
        "created": created,
        "payments_total_rial": row.payments_total_rial,
        "expenses_total_rial": row.expenses_total_rial,
        "net_rial": row.net_rial,
        "payments_count": row.payments_count,
        "expenses_count": row.expenses_count,
    }


def run_daily_finance(db: Session, now: datetime | None = None) -> dict:
    """اجرای idempotent گزارش روزانه برای روز تهرانِ لحظهٔ `now`."""
    now = now or datetime.now(UTC)
    day = tehran_date(now)
    existing = _existing(db, "daily_finance", day)
    if existing is not None:
        return _serialize(existing, created=False)

    numbers = totals(db, day)
    row = ReportRun(
        job_key="daily_finance",
        run_date=day,
        payments_total_rial=numbers["payments_total_rial"],
        expenses_total_rial=numbers["expenses_total_rial"],
        net_rial=numbers["net_rial"],
        payments_count=numbers["payments_count"],
        expenses_count=numbers["expenses_count"],
    )
    try:
        with db.begin_nested():
            db.add(row)
    except IntegrityError:
        # worker دیگر همان روز را ثبت کرد — ردیف او پاسخ درست است.
        db.rollback()
        found = _existing(db, "daily_finance", day)
        if found is None:  # pragma: no cover - یعنی خطا از چیز دیگری بود
            raise
        return _serialize(found, created=False)

    # فقط «آماده است»؛ هیچ مبلغی در ممیزی نوشته نمی‌شود.
    audit(
        db,
        None,
        "scheduled_report_ready",
        "report_run",
        row.id,
        {"job_key": "daily_finance", "run_date": day.isoformat()},
        commit=False,
    )
    db.commit()
    db.refresh(row)
    return _serialize(row, created=True)


def run_job(db: Session, job_key: str, now: datetime | None = None) -> dict:
    if job_key not in JOBS:
        raise ApiError(f"job «{job_key}» شناخته نیست", code="unknown_job")
    return run_daily_finance(db, now=now)


def daily_report(db: Session, run_date: date) -> dict:
    row = _existing(db, "daily_finance", run_date)
    if row is None:
        raise ApiError(
            "برای این تاریخ گزارشی ثبت نشده است", code="report_not_found", status_code=404
        )
    return _serialize(row, created=False)


def next_run_utc(now: datetime | None = None) -> datetime:
    """اجرای بعدی: ۰۰:۱۰ تهران (بعد از ثبت روز قبل) — همیشه در آینده."""
    now = now or datetime.now(UTC)
    local = now.astimezone(TEHRAN)
    candidate = datetime.combine(local.date(), time(0, 10), tzinfo=TEHRAN)
    if candidate <= local:
        candidate += timedelta(days=1)
    return candidate.astimezone(UTC)


def status(db: Session, now: datetime | None = None, limit: int = 10) -> dict:
    now = now or datetime.now(UTC)
    jobs = []
    for key, label in JOBS.items():
        rows = list(
            db.scalars(
                select(ReportRun)
                .where(ReportRun.job_key == key)
                .order_by(ReportRun.run_date.desc())
                .limit(limit)
            )
        )
        jobs.append(
            {
                "job_key": key,
                "label": label,
                "runs": [
                    {
                        "run_date": row.run_date.isoformat(),
                        "net_rial": row.net_rial,
                        "created_at": row.created_at.isoformat() if row.created_at else None,
                    }
                    for row in rows
                ],
            }
        )
    return {
        "jobs": jobs,
        "timezone": "Asia/Tehran",
        "next_run_utc": next_run_utc(now).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

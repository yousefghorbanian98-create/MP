"""گزارش مالی + خروجی CSV + کمیسیون مربی (M27)."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from db.models import Payment, User


def finance_summary(db: Session) -> dict:
    paid = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0)).where(Payment.status == "paid")
    ).scalar()
    pending = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0)).where(Payment.status == "pending")
    ).scalar()
    count_paid = (
        db.execute(
            select(func.count()).select_from(Payment).where(Payment.status == "paid")
        ).scalar()
        or 0
    )
    return {
        "total_paid_rial": int(paid),
        "total_pending_rial": int(pending),
        "paid_count": int(count_paid),
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _safe(v):  # خنثی‌سازی CSV injection برای اکسل
    t = str(v)
    return "'" + t if t and t[0] in "=+-@" else t


def payments_csv(db: Session) -> str:
    rows = db.execute(select(Payment).order_by(Payment.id)).scalars()
    buf = io.StringIO()
    w = csv.writer(buf)  # nosemgrep: use-defusedcsv — خروجی با _safe ضد CSV-injection ضدعفونی می‌شود
    w.writerow(
        ["id", "member_id", "amount_rial", "method", "status", "coach_id", "description", "paid_at"]
    )
    for p in rows:
        w.writerow(
            [
                p.id,
                p.member_id,
                p.amount_rial,
                p.method,
                p.status,
                p.coach_id or "",
                p.description,
                p.paid_at or "",
            ]
        )
    return buf.getvalue()


COMMISSION_RATE_DEFAULT = 0.10  # نرخ پیش‌فرض — قابل تغییر با ورودی (ثبت در گزارش)


def coach_commission(db: Session, coach_id: int, rate: float | None = None) -> dict:
    rate = COMMISSION_RATE_DEFAULT if rate is None else rate
    if not (0 <= rate <= 1):
        from app.errors import ApiError

        raise ApiError("نرخ کمیسیون باید بین ۰ و ۱ باشد", code="invalid_rate")
    coach = db.get(User, coach_id)
    if coach is None:
        from app.errors import NotFoundError

        raise NotFoundError("مربی یافت نشد")
    total = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0)).where(
            Payment.status == "paid", Payment.coach_id == coach_id
        )
    ).scalar()
    return {
        "coach_id": coach_id,
        "coach_name": coach.full_name,
        "rate": rate,
        "attributed_payments_rial": int(total),
        "commission_rial": int(int(total) * rate),
    }

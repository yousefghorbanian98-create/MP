"""گزارش سود/زیان دوره‌ای (QF-10) — هفته، ماه، سال به تقویم جلالی تهران.

# قواعد

- بازه‌ها از تقویم جلالی و منطقهٔ `Asia/Tehran` ساخته می‌شوند؛ ذخیره در UTC می‌ماند.
- هفته از شنبه شروع می‌شود (تقویم رسمی ایران).
- درآمد = پرداخت‌های `paid` که `paid_at` در بازه دارند.
- بازگشت = پرداخت‌های `refunded` که `refunded_at` در بازه دارند؛ در سبد روزِ
  برگشت می‌افتد، نه روز پرداخت اصلی.
- خالص درآمد = درآمد − بازگشت. هزینه = هزینه‌های زنده با `spent_on` در بازه.
- سود = خالص درآمد − هزینه.
- اگر بازگشتی تاریخ ندارد (ثبت قبل از QF-10)، گزارش آن را شمارش و صریحاً گزارش می‌کند؛
  آن را صفر فرض نمی‌کند و سود را «قطعی» اعلام نمی‌کند (`complete=false`).
- `net=0` به معنای «بدهی نیست» نیست؛ این گزارش فقط جمع پول‌های ثبت‌شده است.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.jalali import to_gregorian, to_jalali
from db.models import Expense, Payment

TEHRAN = ZoneInfo("Asia/Tehran")
KINDS = ("week", "month", "year")


@dataclass(frozen=True)
class Window:
    start: date  # شامل
    end: date  # غیرشامل
    label: str


def _jalali_label(y: int, m: int | None = None, d: int | None = None) -> str:
    if m is None:
        return f"{y:04d}"
    if d is None:
        return f"{y:04d}/{m:02d}"
    return f"{y:04d}/{m:02d}/{d:02d}"


def window_for(kind: str, anchor: date) -> Window:
    """بازهٔ دورهٔ شامل `anchor` (تاریخ میلادی)."""
    if kind not in KINDS:
        raise ApiError("نوع دوره باید week|month|year باشد", code="invalid_period_kind")
    jy, jm, jd = to_jalali(anchor.year, anchor.month, anchor.day)
    if kind == "year":
        start = date(*to_gregorian(jy, 1, 1))
        end = date(*to_gregorian(jy + 1, 1, 1))
        label = _jalali_label(jy)
    elif kind == "month":
        start = date(*to_gregorian(jy, jm, 1))
        ny, nm = (jy + 1, 1) if jm == 12 else (jy, jm + 1)
        end = date(*to_gregorian(ny, nm, 1))
        label = _jalali_label(jy, jm)
    else:  # week: شنبه تا جمعه؛ weekday(): دوشنبه=0 … شنبه=5
        offset = (anchor.weekday() - 5) % 7
        start = anchor - timedelta(days=offset)
        end = start + timedelta(days=7)
        sy, sm, sd = to_jalali(start.year, start.month, start.day)
        label = f"هفته‌ای از {_jalali_label(sy, sm, sd)}"
    return Window(start=start, end=end, label=label)


def _utc_bounds(w: Window) -> tuple[datetime, datetime]:
    a = datetime.combine(w.start, time(0, 0), tzinfo=TEHRAN).astimezone(UTC)
    b = datetime.combine(w.end, time(0, 0), tzinfo=TEHRAN).astimezone(UTC)
    return a, b


def period_report(db: Session, kind: str, anchor: date) -> dict:
    w = window_for(kind, anchor)
    start_utc, end_utc = _utc_bounds(w)

    paid_sum, paid_count = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0), func.count(Payment.id)).where(
            Payment.status == "paid",
            Payment.paid_at.is_not(None),
            Payment.paid_at >= start_utc,
            Payment.paid_at < end_utc,
        )
    ).one()
    ref_sum, ref_count = db.execute(
        select(func.coalesce(func.sum(Payment.amount_rial), 0), func.count(Payment.id)).where(
            Payment.status == "refunded",
            Payment.refunded_at.is_not(None),
            Payment.refunded_at >= start_utc,
            Payment.refunded_at < end_utc,
        )
    ).one()
    undated_refunds = int(
        db.scalar(
            select(func.count(Payment.id)).where(
                Payment.status == "refunded", Payment.refunded_at.is_(None)
            )
        )
        or 0
    )
    exp_sum, exp_count = db.execute(
        select(func.coalesce(func.sum(Expense.amount_rial), 0), func.count(Expense.id)).where(
            Expense.deleted_at.is_(None),
            Expense.spent_on >= w.start,
            Expense.spent_on < w.end,
        )
    ).one()

    received = int(paid_sum or 0)
    refunded = int(ref_sum or 0)
    expenses = int(exp_sum or 0)
    net_income = received - refunded
    return {
        "kind": kind,
        "label": w.label,
        "timezone": "Asia/Tehran",
        "start": w.start.isoformat(),
        "end_exclusive": w.end.isoformat(),
        "start_jalali": _jalali_label(*to_jalali(w.start.year, w.start.month, w.start.day)),
        "received_rial": received,
        "received_count": int(paid_count or 0),
        "refunds_rial": refunded,
        "refunds_count": int(ref_count or 0),
        "net_income_rial": net_income,
        "expenses_rial": expenses,
        "expenses_count": int(exp_count or 0),
        "profit_rial": net_income - expenses,
        "undated_refunds_count": undated_refunds,
        "complete": undated_refunds == 0,
    }

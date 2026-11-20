"""هزینهٔ خارجی: ثبت، دوره، اصلاح با دلیل، حذف نرم (QF-06).

# چرا تاریخچهٔ اجباری

هزینه روی سود اثر می‌گذارد؛ اگر عدد بی‌دلیل عوض شود، گزارش مالی بی‌معناست.
پس هر ویرایش دلیل می‌خواهد و مقدار قبل/بعد در `expense_revisions` می‌ماند.
حذف هم نرم است: ردیف از جمع‌ها بیرون می‌رود ولی برای حسابرسی می‌ماند.
"""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import Expense, ExpenseRevision
from db.models.finance import CATEGORIES
from modules.admin.service import audit
from modules.expenses.schemas import ExpenseCreate, ExpenseUpdate

_TRACKED = ("amount_rial", "category", "spent_on", "payee", "note")


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def serialize(row: Expense) -> dict:
    return {
        "id": row.id,
        "amount_rial": row.amount_rial,
        "category": row.category,
        "spent_on": row.spent_on.isoformat()
        if isinstance(row.spent_on, date)
        else str(row.spent_on),
        "payee": row.payee or "",
        "note": row.note or "",
        "created_by_user_id": row.created_by_user_id,
        "created_at": _iso(row.created_at),
        "deleted_at": _iso(row.deleted_at),
    }


def create(db: Session, payload: ExpenseCreate, *, actor) -> Expense:
    row = Expense(
        amount_rial=payload.amount_rial,
        category=payload.category,
        spent_on=payload.spent_on,
        payee=payload.payee,
        note=payload.note,
        created_by_user_id=getattr(actor, "id", None),
    )
    db.add(row)
    db.flush()
    audit(
        db,
        getattr(actor, "id", None),
        "expense_created",
        "expense",
        row.id,
        {"amount_rial": row.amount_rial, "category": row.category},
        commit=False,
    )
    db.commit()
    db.refresh(row)
    return row


def update(db: Session, expense_id: int, payload: ExpenseUpdate, *, actor) -> Expense:
    row = db.get(Expense, expense_id)
    if row is None:
        raise NotFoundError("هزینه پیدا نشد")
    if row.deleted_at is not None:
        raise ApiError("هزینهٔ حذف‌شده قابل اصلاح نیست", code="expense_deleted")

    changes: dict[str, dict[str, object]] = {}
    for field in _TRACKED:
        new_value = getattr(payload, field)
        if new_value is None:
            continue
        old_value = getattr(row, field)
        if field == "spent_on":
            new_value = new_value if isinstance(new_value, date) else new_value
            old_value = old_value if isinstance(old_value, date) else old_value
        if old_value == new_value:
            continue
        changes[field] = {
            "from": old_value.isoformat() if isinstance(old_value, date) else old_value,
            "to": new_value.isoformat() if isinstance(new_value, date) else new_value,
        }
        setattr(row, field, new_value)

    if not changes:
        raise ApiError("هیچ تغییری ارسال نشده است", code="no_changes")

    db.add(
        ExpenseRevision(
            expense_id=row.id,
            reason=payload.reason,
            changes=json.dumps(changes, ensure_ascii=False, sort_keys=True),
            changed_by_user_id=getattr(actor, "id", None),
            created_at=datetime.now(UTC),
        )
    )
    audit(
        db,
        getattr(actor, "id", None),
        "expense_updated",
        "expense",
        row.id,
        {"reason": payload.reason, "fields": sorted(changes)},
        commit=False,
    )
    db.commit()
    db.refresh(row)
    return row


def soft_delete(db: Session, expense_id: int, *, reason: str, actor) -> Expense:
    row = db.get(Expense, expense_id)
    if row is None:
        raise NotFoundError("هزینه پیدا نشد")
    if row.deleted_at is not None:
        raise ApiError("این هزینه قبلاً حذف شده است", code="expense_already_deleted")

    row.deleted_at = datetime.now(UTC)
    row.deleted_by_user_id = getattr(actor, "id", None)
    db.add(
        ExpenseRevision(
            expense_id=row.id,
            reason=reason,
            changes=json.dumps({"deleted": True}, ensure_ascii=False),
            changed_by_user_id=getattr(actor, "id", None),
            created_at=datetime.now(UTC),
        )
    )
    audit(
        db,
        getattr(actor, "id", None),
        "expense_deleted",
        "expense",
        row.id,
        {"reason": reason},
        commit=False,
    )
    db.commit()
    db.refresh(row)
    return row


def period(db: Session, start: date, end: date, category: str | None = None) -> dict:
    """جمع هزینه‌های زندهٔ بازه — به تفکیک دسته و با ریز ردیف‌ها."""
    if end < start:
        raise ApiError("بازهٔ تاریخ نامعتبر است (to قبل از from)", code="invalid_period")

    stmt = select(Expense).where(
        Expense.deleted_at.is_(None),
        Expense.spent_on >= start,
        Expense.spent_on <= end,
    )
    if category:
        stmt = stmt.where(Expense.category == category)
    rows = list(db.scalars(stmt.order_by(Expense.spent_on, Expense.id)))

    totals = db.execute(
        select(Expense.category, func.sum(Expense.amount_rial), func.count(Expense.id))
        .where(
            Expense.deleted_at.is_(None),
            Expense.spent_on >= start,
            Expense.spent_on <= end,
            *([Expense.category == category] if category else []),
        )
        .group_by(Expense.category)
        .order_by(Expense.category)
    ).all()

    return {
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "count": len(rows),
        "total_rial": sum(row.amount_rial for row in rows),
        "by_category": [
            {
                "category": cat,
                "label": CATEGORIES.get(cat, cat),
                "total_rial": int(total or 0),
                "count": int(count or 0),
            }
            for cat, total, count in totals
        ],
        "items": [serialize(row) for row in rows],
    }

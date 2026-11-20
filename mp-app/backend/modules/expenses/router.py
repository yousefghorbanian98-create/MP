"""روتر هزینهٔ خارجی (QF-06).

دو اختیار جدا: `finance.write` برای نوشتن، `finance.read` برای خواندن. نقش‌های
`admin`/`manager` بدون مجوز شخصی فعال، هر دو را ۴۰۳ می‌گیرند (fail-closed).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import CurrentUser, DbSession, require_permission
from app.security.grants import require_grant
from modules.expenses import service
from modules.expenses.schemas import (
    ExpenseCreate,
    ExpenseDelete,
    ExpenseOut,
    ExpensePeriodOut,
    ExpenseUpdate,
)

router = APIRouter(
    prefix="/expenses", tags=["expenses"], dependencies=[Depends(require_permission())]
)


@router.post(
    "",
    response_model=ExpenseOut,
    summary="ثبت هزینهٔ باشگاه (QF-06)",
    dependencies=[Depends(require_grant("finance.write"))],
)
def create_expense(payload: ExpenseCreate, db: DbSession, user: CurrentUser):
    return service.serialize(service.create(db, payload, actor=user))


@router.get(
    "",
    response_model=ExpensePeriodOut,
    summary="هزینه‌های یک دوره با جمع دسته‌بندی‌شده (QF-06)",
    dependencies=[Depends(require_grant("finance.read"))],
)
def list_expenses(
    db: DbSession,
    user: CurrentUser,
    from_date: str = Query(..., alias="from", description="تاریخ شروع (YYYY-MM-DD)"),
    to_date: str = Query(..., alias="to", description="تاریخ پایان (YYYY-MM-DD)"),
    category: str | None = Query(None, max_length=30),
):
    from datetime import date as _date

    try:
        start = _date.fromisoformat(from_date)
        end = _date.fromisoformat(to_date)
    except ValueError as exc:
        from app.errors import ApiError

        raise ApiError("تاریخ باید به شکل YYYY-MM-DD باشد", code="invalid_date") from exc
    return service.period(db, start, end, category)


@router.patch(
    "/{expense_id}",
    response_model=ExpenseOut,
    summary="اصلاح هزینه با دلیل اجباری و تاریخچه (QF-06)",
    dependencies=[Depends(require_grant("finance.write"))],
)
def update_expense(expense_id: int, payload: ExpenseUpdate, db: DbSession, user: CurrentUser):
    return service.serialize(service.update(db, expense_id, payload, actor=user))


@router.delete(
    "/{expense_id}",
    response_model=ExpenseOut,
    summary="حذف نرم هزینه با دلیل (QF-06)",
    dependencies=[Depends(require_grant("finance.write"))],
)
def delete_expense(expense_id: int, payload: ExpenseDelete, db: DbSession, user: CurrentUser):
    return service.serialize(service.soft_delete(db, expense_id, reason=payload.reason, actor=user))

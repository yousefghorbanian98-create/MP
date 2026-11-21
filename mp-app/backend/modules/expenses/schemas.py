"""اسکیمای هزینهٔ خارجی (QF-06)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.money import Rial

Category = Literal[
    "rent",
    "salary",
    "equipment",
    "utilities",
    "maintenance",
    "marketing",
    "tax",
    "other",
]


class ExpenseCreate(BaseModel):
    amount_rial: Rial = Field(..., ge=1000, description="مبلغ به ریال (حداقل ۱٬۰۰۰)")
    category: Category
    spent_on: date
    payee: str = Field("", max_length=120)
    note: str = Field("", max_length=1000)


class ExpenseUpdate(BaseModel):
    """هر تغییر باید دلیل داشته باشد؛ فیلدهای ارسال‌نشده دست‌نخورده می‌مانند."""

    amount_rial: Rial | None = Field(None, ge=1000)
    category: Category | None = None
    spent_on: date | None = None
    payee: str | None = Field(None, max_length=120)
    note: str | None = Field(None, max_length=1000)
    reason: str = Field(..., min_length=3, max_length=200)


class ExpenseDelete(BaseModel):
    reason: str = Field(..., min_length=3, max_length=200)


class ExpenseOut(BaseModel):
    id: int
    amount_rial: int
    category: str
    spent_on: str
    payee: str
    note: str
    created_by_user_id: int | None = None
    created_at: str | None = None
    deleted_at: str | None = None


class CategoryTotal(BaseModel):
    category: str
    label: str
    total_rial: int
    count: int


class ExpensePeriodOut(BaseModel):
    from_date: str
    to_date: str
    count: int
    total_rial: int
    by_category: list[CategoryTotal]
    items: list[ExpenseOut]

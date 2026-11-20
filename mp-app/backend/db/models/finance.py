"""مدل‌های هزینهٔ خارجی باشگاه (QF-06).

هزینه پول عضو نیست، پس در دفتر پول عضو نمی‌آید: این‌جا «پول خارج‌شده» است.
هدف، بسته‌شدن حلقهٔ سود/زیان است — پیش از این فقط درآمد ثبت می‌شد.

# قواعد

- مبلغ **همیشه** ریال صحیح مثبت (بدون اعشار و بدون منفی).
- حذف نرم (`deleted_at`) تا تاریخچه و audit از بین نرود؛ گزارش فقط ردیف‌های زنده را جمع می‌زند.
- هر ویرایش یک ردیف `expense_revisions` با **دلیل اجباری** و تغییرات JSON می‌سازد.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin

CATEGORIES: dict[str, str] = {
    "rent": "اجاره",
    "salary": "حقوق",
    "equipment": "تجهیزات",
    "utilities": "آب/برق/گاز",
    "maintenance": "تعمیر و نگهداری",
    "marketing": "تبلیغات",
    "tax": "مالیات و عوارض",
    "other": "سایر",
}


class Expense(TimestampMixin, Base):
    """یک هزینهٔ واقعی باشگاه؛ فقط-افزودنی از نظر معنایی (حذف نرم)."""

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    amount_rial: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    spent_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payee: Mapped[str] = mapped_column(String(120), nullable=False, server_default="")
    note: Mapped[str] = mapped_column(Text, nullable=False, server_default="")
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ExpenseRevision(Base):
    """تاریخچهٔ اصلاح: دلیل + تغییرات؛ هرگز حذف یا ویرایش نمی‌شود."""

    __tablename__ = "expense_revisions"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    changes: Mapped[str] = mapped_column(Text, nullable=False, server_default="{}")
    changed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ReportRun(Base):
    """اجرای گزارش زمان‌بندی‌شده — کلید یکتا مانع گزارش تکراری در یک روز است (QF-23).

    عددها این‌جا می‌مانند تا اعلان/ممیزی فقط «آماده است» بگوید و مبلغ‌ها فقط از
    endpoint با `finance.read` خوانده شوند.
    """

    __tablename__ = "report_runs"
    __table_args__ = (UniqueConstraint("job_key", "run_date", name="uq_report_runs_job_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    job_key: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payments_total_rial: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    expenses_total_rial: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    net_rial: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    payments_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    expenses_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class ExpenseReceipt(Base):
    """فیش خصوصی یک هزینه (QF-06) — حداکثر یک فایل برای هر هزینه.

    فایل با نام تصادفی بیرون از مسیر استاتیک ذخیره می‌شود؛ فقط از endpoint با
    `finance.read` خوانده می‌شود. حذف هزینه (نرم) فایل را پاک نمی‌کند تا ممیزی بماند.
    """

    __tablename__ = "expense_receipts"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(
        ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    stored_path: Mapped[str] = mapped_column(String(300), nullable=False)
    mime: Mapped[str] = mapped_column(String(30), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

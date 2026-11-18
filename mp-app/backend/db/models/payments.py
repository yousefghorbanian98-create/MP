"""مدل‌های payments — پرداخت، کیف‌پول."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, BranchMixin, TimestampMixin


class Payment(TimestampMixin, BranchMixin, Base):
    """پرداخت — مبلغ به ریال. وضعیت فقط از تأیید درگاه/پذیرش جابه‌جا می‌شود."""

    __tablename__ = "payments"
    __table_args__ = (
        Index(
            "uq_payments_gateway_authority_nonnull",
            "gateway_authority",
            unique=True,
            sqlite_where=text("gateway_authority IS NOT NULL"),
            postgresql_where=text("gateway_authority IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount_rial: Mapped[int] = mapped_column(Integer, nullable=False)
    method: Mapped[str] = mapped_column(
        String(20), nullable=False, default="zarinpal"
    )  # zarinpal | cash | card | wallet
    # pending → paid (verify درگاه) → refunded (M110)؛ `failed` از هر حالت اولیه.
    # ستون رشته‌ای است نه CHECK، پس افزودن وضعیت جدید مهاجرت نمی‌خواهد — ولی
    # `refunded` عمداً از `failed` جداست: «پول آمد و رفت» با «پول نیامد» یکی نیست.
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | paid | failed
    coach_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )  # انتساب مربی (کمیسیون M27)
    reference_id: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    # شناسهٔ تراکنش درگاه (زرین‌پال: authority) — بدون آن، verify نمی‌تواند
    # ثابت کند همین تراکنش را تأیید می‌کند و مبلغ از callback جعلی می‌آمد.
    gateway_authority: Mapped[str | None] = mapped_column(String(80), default=None, nullable=True)
    description: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WalletTransaction(TimestampMixin, BranchMixin, Base):
    """گردش کیف‌پول عضو (شارژ/برداشت)."""

    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    amount_rial: Mapped[int] = mapped_column(Integer, nullable=False)  # مثبت: شارژ، منفی: برداشت
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # credit | debit
    description: Mapped[str] = mapped_column(String(200), default="", nullable=False)

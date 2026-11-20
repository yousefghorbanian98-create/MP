"""مدل‌های payments — پرداخت، کیف‌پول."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
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
        # QF-05 — idempotency: هر (عضو، کلید) تنها یک پرداخت.
        Index(
            "uq_payments_member_idempotency",
            "member_id",
            "idempotency_key",
            unique=True,
            sqlite_where=text("idempotency_key IS NOT NULL"),
            postgresql_where=text("idempotency_key IS NOT NULL"),
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
    refund_reference: Mapped[str | None] = mapped_column(String(80), nullable=True)
    # شناسهٔ تراکنش درگاه (زرین‌پال: authority) — بدون آن، verify نمی‌تواند
    # ثابت کند همین تراکنش را تأیید می‌کند و مبلغ از callback جعلی می‌آمد.
    gateway_authority: Mapped[str | None] = mapped_column(String(80), default=None, nullable=True)
    description: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # QF-09: تأییدکننده نباید پرداختی را که خودش ساخته تأیید کند.
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    # QF-09: پلنی که با تأیید همین پرداخت فعال می‌شود (در همان تراکنش).
    plan_key: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # QF-05: کلید idempotency ارسال دوبارهٔ درخواست توسط اپ را بی‌اثر می‌کند.
    idempotency_key: Mapped[str | None] = mapped_column(String(64), nullable=True)


class PaymentReceipt(Base):
    """فیش کارت‌به‌کارت — فایل خصوصی + صف بازبینی با TTL (QF-07/QF-08).

    فایل هرگز در مسیر عمومی سرو نمی‌شود؛ فقط `stored_path` در DB است و مسیر
    با نام تصادفی ساخته می‌شود. ردیف با رد/تأیید حذف نمی‌شود (ممیزی).
    """

    __tablename__ = "payment_receipts"
    __table_args__ = (
        Index("ix_payment_receipts_payment_id", "payment_id"),
        Index("uq_payment_receipts_review_id", "review_id", unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )
    review_id: Mapped[str] = mapped_column(String(64), nullable=False)
    stored_path: Mapped[str] = mapped_column(String(300), nullable=False)
    mime: Mapped[str] = mapped_column(String(40), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="in_review")
    reject_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


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

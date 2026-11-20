"""مدل‌های payments — پرداخت، کیف‌پول."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, text
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
    # QF-10: «کِی برگشت» جدا از «کِی پرداخت شد». گزارش دوره‌ای بازگشت را در سبد
    # روزِ خودش می‌آورد؛ بدون این ستون، بازگشت به تاریخ پرداخت اصلی چسبانده
    # می‌شد و سودِ دو دوره هر دو غلط می‌شد.
    refunded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
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
    # G2: کوپن اعمال‌شده و مبلغ تخفیف (amount_rial = مبلغ خالص پس از تخفیف)
    coupon_id: Mapped[int | None] = mapped_column(
        ForeignKey("coupons.id", ondelete="SET NULL"), index=True, nullable=True
    )
    discount_rial: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )


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


class LedgerEntry(Base):
    """رویداد دفتر پول عضو — فقط-افزودنی، با مبلغ علامت‌دار (QF-05).

    `amount_rial` مثبت = ورود پول به کیف‌پول، منفی = خروج. حذف ردیف در API
    وجود ندارد؛ اصلاح فقط با ردیف جبرانی (`reverses_entry_id`) انجام می‌شود و
    ردیف اصلی `reversed_by_entry_id` می‌گیرد تا دو بار معکوس نشود.
    """

    __tablename__ = "ledger_entries"
    __table_args__ = (
        Index("ix_ledger_entries_member_id", "member_id"),
        Index(
            "uq_ledger_entries_idempotency",
            "idempotency_key",
            unique=True,
            sqlite_where=text("idempotency_key IS NOT NULL"),
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), nullable=False
    )
    amount_rial: Mapped[int] = mapped_column(Integer, nullable=False)
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # charge | pay | refund | reversal
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)  # wallet | payment
    source_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    reverses_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("ledger_entries.id", ondelete="SET NULL"), nullable=True
    )
    reversed_by_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("ledger_entries.id", ondelete="SET NULL"), nullable=True
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class Coupon(TimestampMixin, Base):
    """کوپن تخفیف — درصدی یا مبلغ ثابت، با تاریخ انقضا و سقف استفاده.

    G2: تخفیف فقط روی سرور و روی مبلغ پرداخت اعمال می‌شود؛ اپ نمی‌تواند
    مبلغ تخفیف را خودش تعیین کند.
    """

    __tablename__ = "coupons"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    # `percent` (۱..۱۰۰) یا `fixed` (ریال)
    kind: Mapped[str] = mapped_column(String(10), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # None یعنی بی‌سقف
    max_uses: Mapped[int | None] = mapped_column(Integer, nullable=True)
    used_count: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("1"), nullable=False
    )

"""اسکیمای payments."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.ids import Id
from app.money import Rial


class PaymentCreate(BaseModel):
    member_id: Id
    amount_rial: Rial = Field(..., ge=1000, description="مبلغ به ریال")
    # درگاه اینترنتی حذف شد؛ فقط روش‌های حضوری و کیف‌پول داخلی.
    method: str = Field("cash", pattern="^(cash|card|card_to_card|wallet)$")
    description: str = Field("", max_length=200)
    # QF-09: پلنی که با تأیید همین پرداخت فعال می‌شود.
    plan_key: str | None = Field(None, max_length=40)
    # QF-05: ارسال دوبارهٔ درخواست با همان کلید، پرداخت دوم نمی‌سازد.
    idempotency_key: str | None = Field(None, min_length=8, max_length=64)
    # G2: کد کوپن اختیاری؛ مبلغ تخفیف فقط روی سرور محاسبه می‌شود.
    coupon_code: str | None = Field(None, min_length=3, max_length=32)


class PaymentVerify(BaseModel):
    reference_id: str = Field("", max_length=80)


class ReceiptReject(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)


class ReceiptOut(BaseModel):
    receipt_id: int
    review_id: str
    payment_id: int
    status: str
    expires_at: str
    size_bytes: int
    mime: str


class ApprovalOut(BaseModel):
    id: int
    member_id: int
    amount_rial: int
    method: str
    status: str
    reference_id: str
    membership_id: int | None = None
    paid_at: str | None = None


class PaymentStartIn(BaseModel):
    callback_url: str = Field("", max_length=300)


class PaymentStartOut(BaseModel):
    payment_id: int
    authority: str
    redirect_url: str
    amount_rial: int
    callback_token: str


class GatewayCallbackIn(BaseModel):
    """callback درگاه: authority + امضای مبلغ؛ هیچ مبلغی از این ورودی پذیرفته نمی‌شود."""

    authority: str = Field("", max_length=80)
    callback_token: str = Field("", max_length=80)


class PaymentOut(BaseModel):
    id: int
    member_id: int
    amount_rial: int
    method: str
    status: str
    reference_id: str
    refund_reference: str | None = None
    gateway_authority: str = ""
    description: str
    paid_at: datetime | None
    discount_rial: int = 0
    coupon_id: int | None = None

    @field_validator("gateway_authority", mode="before")
    @classmethod
    def _empty_missing_authority(cls, value: str | None) -> str:
        return value or ""

    model_config = {"from_attributes": True}


class WalletCharge(BaseModel):
    member_id: Id
    amount_rial: Rial = Field(..., gt=0)
    description: str = Field("", max_length=200)
    # QF-05: تکرار درخواست شارژ از سوی اپ، موجودی را دو بار زیاد نمی‌کند.
    idempotency_key: str | None = Field(None, min_length=8, max_length=80)


class LedgerReverseIn(BaseModel):
    reason: str = Field(..., min_length=3, max_length=200)


class WalletTxOut(BaseModel):
    id: int
    member_id: int
    amount_rial: int
    kind: Literal["credit", "debit"]
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletLedgerOut(BaseModel):
    member_id: int
    balance_rial: int
    transactions: list[WalletTxOut]
    next_before_id: int | None = None


class WalletBalanceOut(BaseModel):
    member_id: int
    balance_rial: int


class CouponCreate(BaseModel):
    code: str = Field(..., min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    kind: str = Field(..., pattern="^(percent|fixed)$")
    value: int = Field(..., ge=1, le=10_000_000_000)
    expires_at: datetime | None = None
    max_uses: int | None = Field(None, ge=1, le=1_000_000)


class CouponOut(BaseModel):
    id: int
    code: str
    kind: str
    value: int
    expires_at: datetime | None
    max_uses: int | None
    used_count: int
    is_active: bool

    model_config = {"from_attributes": True}

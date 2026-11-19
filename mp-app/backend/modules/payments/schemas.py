"""اسکیمای payments."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.ids import Id


class PaymentCreate(BaseModel):
    member_id: Id
    amount_rial: int = Field(..., ge=1000, description="مبلغ به ریال")
    method: str = Field("zarinpal", pattern="^(zarinpal|cash|card|wallet)$")
    description: str = Field("", max_length=200)


class PaymentVerify(BaseModel):
    reference_id: str = Field("", max_length=80)


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

    @field_validator("gateway_authority", mode="before")
    @classmethod
    def _empty_missing_authority(cls, value: str | None) -> str:
        return value or ""

    model_config = {"from_attributes": True}


class WalletCharge(BaseModel):
    member_id: Id
    amount_rial: int = Field(..., gt=0)
    description: str = Field("", max_length=200)


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

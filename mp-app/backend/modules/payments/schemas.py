"""اسکیمای payments."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

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
    gateway_authority: str = ""
    description: str
    paid_at: datetime | None

    model_config = {"from_attributes": True}


class WalletCharge(BaseModel):
    member_id: Id
    amount_rial: int = Field(..., gt=0)
    description: str = Field("", max_length=200)


class WalletTxOut(BaseModel):
    id: int
    member_id: int
    amount_rial: int
    kind: str
    description: str

    model_config = {"from_attributes": True}


class WalletBalanceOut(BaseModel):
    member_id: int
    balance_rial: int

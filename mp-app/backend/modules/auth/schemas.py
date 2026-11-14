"""اسکیمای Pydantic ماژول auth."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator

PHONE_RE = re.compile(r"^09\d{9}$")


class OtpRequest(BaseModel):
    phone: str = Field(
        ..., description="شماره موبایل ایران (09xxxxxxxxx)", examples=["09121234567"]
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not PHONE_RE.match(v):
            raise ValueError("شمارهٔ موبایل معتبر نیست (مثال: 09121234567)")
        return v


class OtpRequestResponse(BaseModel):
    phone: str
    expires_in: int
    dev_code: str | None = Field(None, description="فقط در محیط development برای تست")


class OtpVerify(BaseModel):
    phone: str
    code: str = Field(..., min_length=6, max_length=6, description="کد ۶ رقمی")


class UserBrief(BaseModel):
    id: int
    phone: str
    role: str
    full_name: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserBrief | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class MessageResponse(BaseModel):
    status: str

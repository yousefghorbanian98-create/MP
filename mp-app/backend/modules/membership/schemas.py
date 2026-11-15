"""اسکیمای membership."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemberCreate(BaseModel):
    phone: str = Field(..., pattern=r"^09\d{9}$")
    full_name: str = Field(..., min_length=2, max_length=120)
    goal: str = Field("", max_length=30)
    gender: Literal["male", "female"] = Field(..., description="جنسیت اجباری — تفکیک آقایان/بانوان (M41-c1)")
    height_cm: int | None = Field(None, ge=100, le=250)
    constraints: str = Field("[]", description="JSON آسیب‌ها/محدودیت‌ها")


class MemberUpdate(BaseModel):
    full_name: str | None = None
    goal: str | None = None
    gender: str | None = None
    height_cm: int | None = Field(None, ge=100, le=250)
    constraints: str | None = None
    emergency_contact: str | None = None
    birth_date: date | None = None


class MemberOut(BaseModel):
    id: int
    user_id: int
    branch_id: int
    goal: str
    gender: str
    height_cm: int | None
    constraints: str

    model_config = {"from_attributes": True}


class MembershipCreate(BaseModel):
    member_id: int
    plan_name: str = Field(..., min_length=2, max_length=60)
    duration_days: int = Field(..., ge=1, le=730)
    price_rial: int = Field(..., ge=0)


class MembershipOut(BaseModel):
    id: int
    member_id: int
    plan_name: str
    started_at: datetime
    expires_at: datetime
    status: str
    price_rial: int

    model_config = {"from_attributes": True}

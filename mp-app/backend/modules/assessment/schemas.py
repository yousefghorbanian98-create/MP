"""اسکیمای assessment."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.ids import Id


class DomainScoreIn(BaseModel):
    domain: int = Field(..., ge=1, le=14)
    score: int = Field(..., ge=0, le=5)
    notes: str = Field("", max_length=500)


class AssessmentCreate(BaseModel):
    member_id: Id
    scores: list[DomainScoreIn] = Field(..., min_length=14, max_length=14)
    notes: str = Field("", max_length=2000)


class DomainScoreOut(BaseModel):
    domain: int
    score: int
    notes: str

    model_config = {"from_attributes": True}


class AssessmentOut(BaseModel):
    id: int
    member_id: int
    coach_id: int | None
    total_score: int
    flags: str
    notes: str
    scores: list[DomainScoreOut] = []

    model_config = {"from_attributes": True}


class Jp7In(BaseModel):
    member_id: Id
    age: int = Field(..., ge=10, le=100)
    gender: str = Field(..., pattern="^(male|female)$")
    skinfolds_mm: dict[str, float] = Field(
        ...,
        description="۷ چین: chest, triceps, subscapular, suprailiac, abdomen, thigh, calf (خام، mm)",
    )
    quality: str | None = Field(None, max_length=32, description="کیفیت اندازه‌گیری (E02)")
    method: str | None = Field(None, max_length=64, description="روش/ابزار (E02)")


class Jp7Out(BaseModel):
    id: int
    member_id: int
    age: int
    gender: str
    skinfolds_mm: str
    body_fat_pct: float | None = None  # قفل تا مرجع مستقل (D-012) — None = نامعلوم
    equation_version: str
    quality: str | None = None
    method: str | None = None
    measured_at: datetime

    model_config = {"from_attributes": True}


class LimbMeasurementIn(BaseModel):
    """M54-c1 — محیط اندام (cm). همه اختیاری؛ حداقل یکی لازم است."""

    member_id: Id
    neck_cm: float | None = Field(default=None, gt=0, le=300)
    chest_cm: float | None = Field(default=None, gt=0, le=300)
    waist_cm: float | None = Field(default=None, gt=0, le=300)
    hip_cm: float | None = Field(default=None, gt=0, le=300)
    upper_arm_right_cm: float | None = Field(default=None, gt=0, le=300)
    upper_arm_left_cm: float | None = Field(default=None, gt=0, le=300)
    thigh_right_cm: float | None = Field(default=None, gt=0, le=300)
    thigh_left_cm: float | None = Field(default=None, gt=0, le=300)
    calf_right_cm: float | None = Field(default=None, gt=0, le=300)
    calf_left_cm: float | None = Field(default=None, gt=0, le=300)
    quality: str | None = Field(default=None, max_length=32)
    notes: str = Field(default="", max_length=500)

"""اسکیمای assessment."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DomainScoreIn(BaseModel):
    domain: int = Field(..., ge=1, le=14)
    score: int = Field(..., ge=0, le=5)
    notes: str = Field("", max_length=500)


class AssessmentCreate(BaseModel):
    member_id: int
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
    member_id: int
    age: int = Field(..., ge=10, le=100)
    gender: str = Field(..., pattern="^(male|female)$")
    skinfolds_mm: dict[str, float] = Field(
        ..., description="۷ چین: chest, triceps, subscapular, suprailiac, abdomen, thigh, calf"
    )


class Jp7Out(BaseModel):
    id: int
    member_id: int
    age: int
    gender: str
    skinfolds_mm: str
    body_fat_pct: float
    measured_at: datetime

    model_config = {"from_attributes": True}

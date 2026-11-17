"""اسکیمای ai_engine."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ids import Id


class ProgramGenerateIn(BaseModel):
    member_id: Id
    goal: str = Field(..., pattern="^(hypertrophy|strength|weight_loss|fitness)$")
    level: str = Field(..., pattern="^(beginner|intermediate|advanced)$")
    days_per_week: int = Field(3, ge=3, le=6)
    weeks_count: int = Field(8, ge=1, le=24)
    constraints: list[str] = Field(default_factory=list, max_length=5)


class NutritionGenerateIn(BaseModel):
    member_id: Id
    goal: str = Field(..., pattern="^(hypertrophy|strength|weight_loss|fitness)$")
    activity: str = Field(..., pattern="^(sedentary|light|moderate|active|athlete)$")
    weight_kg: float = Field(..., gt=20, le=400)
    height_cm: float = Field(..., gt=80, le=260)
    age: int = Field(..., ge=10, le=100)
    gender: str = Field(..., pattern="^(male|female)$")

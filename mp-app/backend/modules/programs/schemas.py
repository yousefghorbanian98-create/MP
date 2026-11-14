"""اسکیمای programs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProgramExerciseOut(BaseModel):
    id: int
    exercise_id: int
    day: int
    order: int
    sets: int
    reps: str
    load_pct: int
    rest_seconds: int
    notes: str

    model_config = {"from_attributes": True}


class ProgramWeekOut(BaseModel):
    id: int
    week_number: int
    focus: str
    exercises: list[ProgramExerciseOut] = []

    model_config = {"from_attributes": True}


class ProgramOut(BaseModel):
    id: int
    member_id: int
    coach_id: int | None
    status: str
    goal: str
    engine_version: str
    llm_explanation: str
    reject_reason: str
    approved_at: datetime | None
    weeks: list[ProgramWeekOut] = []

    model_config = {"from_attributes": True}


class RejectIn(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)

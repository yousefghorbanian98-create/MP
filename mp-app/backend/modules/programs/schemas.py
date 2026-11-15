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
    # M46-c4 — چه کسی تأیید/رد کرد؛ پیش‌تر در پاسخ نبود و UI نمی‌توانست نشان دهد
    approved_by: int | None = None
    # Q7 — نتیجهٔ غربالگری ایمنی به‌صورت متن JSON (safety-1.0).
    # «{}» یعنی غربالگری انجام نشده — با «بی‌خطر» یکی نیست.
    safety_flags: str = "{}"
    weeks: list[ProgramWeekOut] = []

    model_config = {"from_attributes": True}


class RejectIn(BaseModel):
    reason: str = Field(..., min_length=3, max_length=1000)


class EngineExerciseIn(BaseModel):
    exercise_id: int
    day: int = Field(..., ge=1, le=7)
    order: int = Field(0, ge=0, le=20)
    sets: int = Field(..., ge=1, le=20)
    reps: str = Field(..., min_length=1, max_length=20)
    load_pct: int = Field(0, ge=0, le=120)
    rest_seconds: int = Field(60, ge=0, le=600)
    notes: str = Field("", max_length=300)


class EngineWeekIn(BaseModel):
    week_number: int = Field(..., ge=1, le=52)
    focus: str = Field("", max_length=120)
    exercises: list[EngineExerciseIn] = Field(default_factory=list)


class ProgramFromEngineIn(BaseModel):
    member_id: int
    goal: str = Field("", max_length=60)
    engine_version: str = Field("", max_length=20)
    llm_explanation: str = Field("", max_length=5000)  # فقط متن — هرگز عدد (G8)
    weeks: list[EngineWeekIn] = Field(default_factory=list)


class SetFeedbackEntryIn(BaseModel):
    movement_id: str = Field(min_length=1, max_length=60)
    weight: float = Field(ge=0)  # صفر = حرکت وزن‌بدن
    target_reps: int = Field(ge=1)
    reps_done: int = Field(ge=0)
    rir: float | None = Field(default=None, ge=0, le=10)
    soreness: int | None = Field(default=None, ge=0, le=10)
    # G2 — تعداد ستی که عضو واقعاً انجام داد. اختیاری و صریح: اگر خالی باشد
    # موتور هیچ عدد حجمی از «تعداد ردیف‌های ارسالی» نمی‌سازد (باگ ۲۰).
    sets_done: int | None = Field(default=None, ge=0, le=40)
    notes: str = ""


class SetFeedbackIn(BaseModel):
    member_id: int
    program_id: int | None = None
    entries: list[SetFeedbackEntryIn] = Field(min_length=1)

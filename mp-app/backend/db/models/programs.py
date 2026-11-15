"""مدل‌های programs — برنامهٔ تمرین (با گردش کاری تأیید مربی)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, BranchMixin, TimestampMixin


class WorkoutProgram(TimestampMixin, BranchMixin, Base):
    """برنامهٔ تمرین — خروجی موتور قواعد، تأییدشده توسط مربی.

    گردش کاری: draft → (تأیید مربی) approved | (رد) rejected → نمایش عضو.
    اعداد فقط از موتور قواعد می‌آیند (G8) — LLM فقط توضیح می‌نویسد.
    """

    __tablename__ = "workout_programs"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    coach_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )  # draft | approved | rejected
    goal: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    llm_explanation: Mapped[str] = mapped_column(
        Text, default="", nullable=False
    )  # فقط متن — هرگز عدد
    reject_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Q7 — نتیجهٔ غربالگری ایمنی به‌صورت JSON (safety-1.0).
    # "{}" یعنی غربالگری انجام نشده؛ با "status: unknown" یکی نیست.
    safety_flags: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    weeks: Mapped[list[ProgramWeek]] = relationship(
        back_populates="program", cascade="all, delete-orphan"
    )


class ProgramWeek(Base):
    """یک هفته از برنامه."""

    __tablename__ = "program_weeks"

    id: Mapped[int] = mapped_column(primary_key=True)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("workout_programs.id", ondelete="CASCADE"), index=True, nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    focus: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    program: Mapped[WorkoutProgram] = relationship(back_populates="weeks")
    exercises: Mapped[list[ProgramExercise]] = relationship(
        back_populates="week", cascade="all, delete-orphan"
    )


class ProgramExercise(Base):
    """یک حرکت برنامه‌ریزی‌شده (بار/ست/تکرار — فقط از موتور قواعد)."""

    __tablename__ = "program_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    week_id: Mapped[int] = mapped_column(
        ForeignKey("program_weeks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    exercise_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False
    )
    day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..7
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[str] = mapped_column(String(20), nullable=False)  # مثلاً "8-12" یا "30s"
    load_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # %1RM
    rest_seconds: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    week: Mapped[ProgramWeek] = relationship(back_populates="exercises")


class SetFeedback(TimestampMixin, BranchMixin, Base):
    """بازخورد ست‌به‌ست (G1 — M38-c2): RIR/درد هر ست برای تنظیم هفتگی."""

    __tablename__ = "set_feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    program_id: Mapped[int | None] = mapped_column(
        ForeignKey("workout_programs.id", ondelete="SET NULL"), nullable=True
    )
    movement_id: Mapped[str] = mapped_column(String(60), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    target_reps: Mapped[int] = mapped_column(Integer, nullable=False)
    reps_done: Mapped[int] = mapped_column(Integer, nullable=False)
    # RIR (تکرار ذخیره) و درد عضلانی ۰..۱۰ — خودگزارش
    rir: Mapped[float | None] = mapped_column(Float, nullable=True)
    soreness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

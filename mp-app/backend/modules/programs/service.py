"""سرویس programs — گردش کاری برنامه (draft → تأیید/رد مربی).

قاعدهٔ G8: تولید اعداد (بار/ست/تکرار) فقط در ai_engine (M15) انجام می‌شود؛
این سرویس فقط مدیریت چرخهٔ وضعیت و ثبت تغییرات را انجام می‌دهد.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import ProgramExercise, ProgramWeek, WorkoutProgram


def get_program(db: Session, program_id: int) -> WorkoutProgram:
    p = db.get(WorkoutProgram, program_id)
    if p is None:
        raise NotFoundError("برنامه یافت نشد")
    return p


def list_member_programs(db: Session, member_id: int) -> list[WorkoutProgram]:
    return list(
        db.scalars(
            select(WorkoutProgram)
            .where(WorkoutProgram.member_id == member_id)
            .order_by(WorkoutProgram.id.desc())
        )
    )


def approve_program(db: Session, program_id: int, coach_id: int) -> WorkoutProgram:
    """تأیید مربی (US-203) — فقط draft قابل تأیید است."""
    p = get_program(db, program_id)
    if p.status != "draft":
        raise ApiError("فقط برنامهٔ draft قابل تأیید است", code="invalid_status")
    p.status = "approved"
    p.approved_at = datetime.now(UTC)
    p.approved_by = coach_id
    db.commit()
    db.refresh(p)
    return p


def reject_program(db: Session, program_id: int, coach_id: int, reason: str) -> WorkoutProgram:
    p = get_program(db, program_id)
    if p.status != "draft":
        raise ApiError("فقط برنامهٔ draft قابل رد است", code="invalid_status")
    if not reason.strip():
        raise ApiError("دلیل رد الزامی است", code="reason_required")
    p.status = "rejected"
    p.reject_reason = reason
    p.approved_by = coach_id
    db.commit()
    db.refresh(p)
    return p


def create_program_from_engine_output(
    db: Session,
    member_id: int,
    engine_output: dict,
    coach_id: int | None = None,
) -> WorkoutProgram:
    """ثبت خروجی موتور قواعد به‌صورت برنامهٔ draft (توسط ai_engine/M15 فراخوانی می‌شود).

    ساختار engine_output: {'goal': str, 'engine_version': str, 'weeks': [
      {'week_number': 1, 'focus': str, 'exercises': [
        {'exercise_id': 1, 'day': 1, 'order': 0, 'sets': 3, 'reps': '8-12',
         'load_pct': 70, 'rest_seconds': 90, 'notes': ''}]}]}
    """
    program = WorkoutProgram(
        member_id=member_id,
        coach_id=coach_id,
        goal=engine_output.get("goal", ""),
        engine_version=engine_output.get("engine_version", ""),
        llm_explanation=engine_output.get("llm_explanation", ""),  # فقط متن — هرگز عدد (G8)
        status="draft",
        branch_id=1,
    )
    db.add(program)
    db.flush()
    for week in engine_output.get("weeks", []):
        w = ProgramWeek(
            program_id=program.id,
            week_number=week["week_number"],
            focus=week.get("focus", ""),
        )
        db.add(w)
        db.flush()
        for ex in week.get("exercises", []):
            db.add(
                ProgramExercise(
                    week_id=w.id,
                    exercise_id=ex["exercise_id"],
                    day=ex["day"],
                    order=ex.get("order", 0),
                    sets=ex["sets"],
                    reps=ex["reps"],
                    load_pct=ex.get("load_pct", 0),
                    rest_seconds=ex.get("rest_seconds", 60),
                    notes=ex.get("notes", ""),
                )
            )
    db.commit()
    db.refresh(program)
    return program

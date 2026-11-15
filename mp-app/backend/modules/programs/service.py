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


def get_program(db: Session, program_id: int, user=None) -> WorkoutProgram:
    p = db.get(WorkoutProgram, program_id)
    from app.security.ownership import ensure_record_scope

    ensure_record_scope(db, user, p)
    if p is None:
        raise NotFoundError("برنامه یافت نشد")
    return p


def list_member_programs(db: Session, member_id: int, user=None) -> list[WorkoutProgram]:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
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
    from modules.admin.service import audit

    audit(db, coach_id, "program_approved", "workout_program", p.id, {})
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
    from modules.admin.service import audit

    audit(db, coach_id, "program_rejected", "workout_program", p.id, {"reason": reason})
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

    # M46-c4 — پیش از درج حرکات، کاتالوگ را تضمین کن.
    # `program_exercises.exercise_id` یک FK واقعی است و LIBRARY موتور
    # هیچ seedی در DB نداشت؛ نتیجه ردیف یتیم (FK خاموش) یا ۵۰۰ (FK روشن).
    from engine.catalog_sync import ensure_exercises

    ensure_exercises(
        db,
        {
            ex["exercise_id"]
            for week in engine_output.get("weeks", [])
            for ex in week.get("exercises", [])
            if "exercise_id" in ex
        },
    )

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


def record_set_feedback(
    db: Session,
    *,
    member_id: int,
    program_id: int | None,
    entries: list[dict],
    user=None,
) -> dict:
    """ثبت بازخورد ست‌ها + پیشنهاد جلسهٔ بعد (G1 — M38-c2)."""
    from app.security.ownership import ensure_member_scope
    from db.models.programs import SetFeedback
    from engine.set_feedback import process_set_feedback

    ensure_member_scope(db, user, member_id)
    for entry in entries:
        db.add(
            SetFeedback(
                member_id=member_id,
                program_id=program_id,
                movement_id=entry["movement_id"],
                weight=entry["weight"],
                target_reps=entry["target_reps"],
                reps_done=entry["reps_done"],
                rir=entry.get("rir"),
                soreness=entry.get("soreness"),
                notes=entry.get("notes", ""),
            )
        )
    db.commit()
    return process_set_feedback(entries=entries)


PROGRAMS_SUMMARY_VERSION = "programs-summary-1.0"


def list_programs_summary(db, *, status: str | None = None, limit: int = 200) -> dict:
    """فهرست برنامه‌های باشگاه با نام عضو — برای صفحهٔ «برنامه‌ها» در استودیو.

    فقط برنامه‌های واقعی برمی‌گردند؛ فهرست خالی یعنی «برنامه‌ای ثبت نشده»،
    نه اینکه با داده‌ی نمایشی پر شود.
    """
    from sqlalchemy import select

    from db.models import Member, User, WorkoutProgram

    stmt = select(WorkoutProgram).order_by(WorkoutProgram.id.desc()).limit(limit)
    if status:
        stmt = stmt.where(WorkoutProgram.status == status)
    programs = db.scalars(stmt).all()

    member_ids = {p.member_id for p in programs}
    names: dict[int, str] = {}
    if member_ids:
        rows = db.execute(
            select(Member.id, User.full_name)
            .join(User, User.id == Member.user_id)
            .where(Member.id.in_(member_ids))
        ).all()
        names = dict(rows)

    items = [
        {
            "id": p.id,
            "member_id": p.member_id,
            "member_name": names.get(p.member_id, ""),
            "status": p.status,
            "goal": p.goal,
            "engine_version": p.engine_version,
            "weeks_count": len(p.weeks) if p.weeks is not None else 0,
            "llm_explanation": p.llm_explanation,
            "reject_reason": p.reject_reason,
            "approved_at": p.approved_at.isoformat() if p.approved_at else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in programs
    ]
    return {
        "items": items,
        "rule_version": PROGRAMS_SUMMARY_VERSION,
        "counts_by_status": {
            s: sum(1 for i in items if i["status"] == s) for s in {i["status"] for i in items}
        },
    }

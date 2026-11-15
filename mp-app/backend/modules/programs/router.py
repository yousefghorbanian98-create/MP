"""روتر programs — مشاهده و گردش کاری تأیید مربی (تولید در M15 با ai_engine)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import CurrentUser, DbSession, require_permission
from modules.programs import service
from modules.programs.schemas import ProgramFromEngineIn, ProgramOut, RejectIn, SetFeedbackIn

router = APIRouter(
    prefix="/programs", tags=["programs"], dependencies=[Depends(require_permission())]
)


# ── M45-c2: فهرست برنامه‌های باشگاه برای استودیو (جایگزین mock) [finn] ──


@router.get("", summary="فهرست برنامه‌های باشگاه با وضعیت گردش کاری (M45-c2)")
def list_programs(
    db: DbSession,
    status: str | None = None,
    limit: int = 200,
):
    return service.list_programs_summary(db, status=status, limit=limit)


@router.get(
    "/member/{member_id}", response_model=list[ProgramOut], summary="برنامه‌های عضو (US-104)"
)
def list_member_programs(member_id: int, db: DbSession, user: CurrentUser):
    return service.list_member_programs(db, member_id, user=user)


@router.post(
    "/from-engine",
    response_model=ProgramOut,
    summary="ثبت خروجی موتور قواعد به‌صورت draft (G8 — M15)",
)
def create_from_engine(payload: ProgramFromEngineIn, db: DbSession, user: CurrentUser):
    # M46-c4 — coach_id از JWT واقعی، نه None/0 (بی‌صدا در FK خاموش گم می‌شد)
    return service.create_program_from_engine_output(
        db, payload.member_id, payload.model_dump(), coach_id=user.id
    )


@router.get("/{program_id}", response_model=ProgramOut, summary="جزئیات برنامه")
def get_program(program_id: int, db: DbSession, user: CurrentUser):
    return service.get_program(db, program_id, user=user)


@router.post(
    "/{program_id}/approve", response_model=ProgramOut, summary="تأیید برنامه توسط مربی (US-203)"
)
def approve_program(program_id: int, db: DbSession, user: CurrentUser):
    # M46-c4 — پیش‌تر `coach_id=0  # M08: coach_id واقعی از JWT` بود: یک TODO
    # که هرگز انجام نشد و ستون approved_by را با ۰ (کاربر ناموجود) پر می‌کرد.
    return service.approve_program(db, program_id, coach_id=user.id)


@router.post(
    "/{program_id}/reject", response_model=ProgramOut, summary="رد برنامه با دلیل (US-203)"
)
def reject_program(program_id: int, payload: RejectIn, db: DbSession, user: CurrentUser):
    return service.reject_program(db, program_id, coach_id=user.id, reason=payload.reason)


@router.get(
    "/member/{member_id}/readiness",
    summary="امتیاز آمادگی/خستگی از بازخورد واقعی + توصیهٔ کاهش خودکار حجم (G13)",
)
def member_readiness(member_id: int, db: DbSession, user: CurrentUser):
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    return service.readiness_report(db, member_id=member_id)


@router.get(
    "/member/{member_id}/volume",
    summary="حجم هفتگی هر گروه عضلانی + نشانگرهای MV/MEV/MAV/MRV (G2)",
)
def member_volume(
    member_id: int,
    db: DbSession,
    user: CurrentUser,
    level: str = "intermediate",
):
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    return service.weekly_volume_report(db, member_id=member_id, level=level)


@router.post("/set-feedback", summary="ثبت بازخورد ست‌به‌ست (RIR/درد) + پیشنهاد جلسهٔ بعد (G1)")
def set_feedback(payload: SetFeedbackIn, db: DbSession, user: CurrentUser):
    return service.record_set_feedback(
        db,
        member_id=payload.member_id,
        program_id=payload.program_id,
        entries=[e.model_dump() for e in payload.entries],
        user=user,
    )


# ── G7 — همگام‌سازی صف آفلاین ──


class SyncItemIn(BaseModel):
    client_id: str = Field(min_length=1, max_length=64)
    # برنامه‌ای که این ست به آن تعلق دارد — بدون آن، بازخورد آفلاین
    # هیچ‌گاه به برنامه وصل نمی‌شد و G13 آمادگی برایش null می‌داد.
    program_id: int | None = None
    device_id: str = Field(min_length=1, max_length=64)
    updated_at: datetime
    movement_id: str = Field(default="", max_length=60)
    weight: float = Field(default=0, ge=0)
    target_reps: int = Field(default=0, ge=0)
    reps_done: int = Field(default=0, ge=0)
    rir: float | None = None
    soreness: int | None = None
    notes: str = Field(default="", max_length=500)


class SyncIn(BaseModel):
    member_id: int = Field(ge=1)
    items: list[SyncItemIn] = Field(default_factory=list, max_length=500)


@router.post("/sync/set-feedback", summary="همگام‌سازی صف آفلاین بازخورد ست (G7 — LWW)")
def sync_set_feedback(payload: SyncIn, db: DbSession, user: CurrentUser):
    return service.sync_set_feedback(
        db,
        member_id=payload.member_id,
        items=[i.model_dump() for i in payload.items],
        user=user,
    )

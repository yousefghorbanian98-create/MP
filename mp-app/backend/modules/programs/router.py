"""روتر programs — مشاهده و گردش کاری تأیید مربی (تولید در M15 با ai_engine)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import DbSession, require_permission
from modules.programs import service
from modules.programs.schemas import ProgramFromEngineIn, ProgramOut, RejectIn

router = APIRouter(
    prefix="/programs", tags=["programs"], dependencies=[Depends(require_permission())]
)


@router.get(
    "/member/{member_id}", response_model=list[ProgramOut], summary="برنامه‌های عضو (US-104)"
)
def list_member_programs(member_id: int, db: DbSession):
    return service.list_member_programs(db, member_id)


@router.post(
    "/from-engine",
    response_model=ProgramOut,
    summary="ثبت خروجی موتور قواعد به‌صورت draft (G8 — M15)",
)
def create_from_engine(payload: ProgramFromEngineIn, db: DbSession):
    return service.create_program_from_engine_output(
        db, payload.member_id, payload.model_dump(), coach_id=None
    )


@router.get("/{program_id}", response_model=ProgramOut, summary="جزئیات برنامه")
def get_program(program_id: int, db: DbSession):
    return service.get_program(db, program_id)


@router.post(
    "/{program_id}/approve", response_model=ProgramOut, summary="تأیید برنامه توسط مربی (US-203)"
)
def approve_program(program_id: int, db: DbSession):
    return service.approve_program(db, program_id, coach_id=0)  # M08: coach_id واقعی از JWT


@router.post(
    "/{program_id}/reject", response_model=ProgramOut, summary="رد برنامه با دلیل (US-203)"
)
def reject_program(program_id: int, payload: RejectIn, db: DbSession):
    return service.reject_program(db, program_id, coach_id=0, reason=payload.reason)

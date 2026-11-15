"""روتر ارزیابی ۱۴ توانایی (M36) — RBAC با casbin + مالکیت در service."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, DbSession, require_permission
from modules.axis_assessment import service
from modules.axis_assessment.schemas import AssessmentCreate, MatrixOut

router = APIRouter(
    prefix="/axis-assessments",
    tags=["axis-assessment"],
    dependencies=[Depends(require_permission())],
)


@router.post("", response_model=MatrixOut, summary="ثبت جلسهٔ ارزیابی ۱۴ توانایی با آزمون‌های میدانی")
def create_assessment(payload: AssessmentCreate, db: DbSession, user: CurrentUser):
    return service.create_assessment(
        db,
        member_id=payload.member_id,
        tests=[t.model_dump() for t in payload.tests],
        notes=payload.notes,
        user=user,
    )


@router.get("/{assessment_id}/matrix", response_model=MatrixOut, summary="ماتریس درصد ۱۴ محور + تصمیم")
def get_matrix(assessment_id: int, db: DbSession, user: CurrentUser):
    return service.get_matrix(db, assessment_id, user=user)


@router.get("/member/{member_id}", summary="تاریخچهٔ ارزیابی‌های ۱۴ توانایی عضو")
def list_member_history(member_id: int, db: DbSession, user: CurrentUser):
    return service.list_member_history(db, member_id, user=user)

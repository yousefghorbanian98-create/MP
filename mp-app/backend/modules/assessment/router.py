"""روتر assessment."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import DbSession, require_permission
from modules.assessment import service
from modules.assessment.schemas import AssessmentCreate, AssessmentOut, Jp7In, Jp7Out

router = APIRouter(
    prefix="/assessments", tags=["assessment"], dependencies=[Depends(require_permission())]
)


@router.post("", response_model=AssessmentOut, summary="ثبت ارزیابی ۱۴ دامنه (US-201)")
def create_assessment(payload: AssessmentCreate, db: DbSession):
    return service.create_assessment(
        db,
        member_id=payload.member_id,
        scores=[s.model_dump() for s in payload.scores],
        notes=payload.notes,
    )


@router.get("/{assessment_id}", response_model=AssessmentOut, summary="جزئیات ارزیابی")
def get_assessment(assessment_id: int, db: DbSession):
    return service.get_assessment(db, assessment_id)


@router.get(
    "/member/{member_id}",
    response_model=list[AssessmentOut],
    summary="تاریخچهٔ ارزیابی‌های عضو",
)
def list_member_assessments(member_id: int, db: DbSession):
    return service.list_member_assessments(db, member_id)


@router.post("/jp7", response_model=Jp7Out, summary="ثبت اندازه‌گیری JP7 (US-202)")
def record_jp7(payload: Jp7In, db: DbSession):
    return service.record_jp7(
        db,
        member_id=payload.member_id,
        skinfolds_mm=payload.skinfolds_mm,
        age=payload.age,
        gender=payload.gender,
    )

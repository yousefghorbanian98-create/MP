"""روتر assessment."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, DbSession, require_permission
from modules.assessment import service
from modules.assessment.schemas import (
    AssessmentCreate,
    AssessmentOut,
    Jp7In,
    Jp7Out,
    LimbMeasurementIn,
)

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
def get_assessment(assessment_id: int, db: DbSession, user: CurrentUser):
    return service.get_assessment(db, assessment_id, user=user)


@router.get(
    "/member/{member_id}",
    response_model=list[AssessmentOut],
    summary="تاریخچهٔ ارزیابی‌های عضو",
)
def list_member_assessments(member_id: int, db: DbSession, user: CurrentUser):
    return service.list_member_assessments(db, member_id, user=user)


@router.post("/jp7", response_model=Jp7Out, summary="ثبت اندازه‌گیری JP7 (US-202)")
def record_jp7(payload: Jp7In, db: DbSession):
    return service.record_jp7(
        db,
        member_id=payload.member_id,
        skinfolds_mm=payload.skinfolds_mm,
        age=payload.age,
        gender=payload.gender,
        quality=payload.quality,
        method=payload.method,
    )


# ── G6 — روندنمای JP7 + تفسیر خودکار [finn] ──


@router.get(
    "/jp7/member/{member_id}/trend",
    summary="روند چین‌های پوستی + تفسیر خودکار (G6)",
)
def jp7_trend(member_id: int, db: DbSession, user: CurrentUser):
    return service.jp7_trend(db, member_id=member_id, user=user)


# ── M54-c1 — آنالیز سگمنتال آنتروپومتریک (D-024) ──


@router.post("/limb", summary="ثبت محیط اندام (سگمنتال آنتروپومتریک)")
def record_limb(payload: LimbMeasurementIn, db: DbSession, user: CurrentUser):
    row = service.record_limb_measurement(
        db,
        member_id=payload.member_id,
        values=payload.model_dump(exclude={"member_id", "quality", "notes"}),
        user=user,
        quality=payload.quality,
        notes=payload.notes,
    )
    return service.limb_dict(row)


@router.get(
    "/limb/member/{member_id}/report",
    summary="تحلیل سگمنتال + روند محیط اندام",
)
def segmental_report(member_id: int, db: DbSession, user: CurrentUser):
    return service.segmental_report(db, member_id=member_id, user=user)

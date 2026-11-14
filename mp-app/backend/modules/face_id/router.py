"""روتر face_id — رضایت، چهره، چک‌این."""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends

from app.deps import CurrentUser, DbSession, require_permission
from modules.face_id import service
from modules.face_id.schemas import (
    CheckInIn,
    CheckInOut,
    ConsentIn,
    ConsentOut,
    FaceEnroll,
    FaceTemplateOut,
)

router = APIRouter(prefix="/face", tags=["face-id"], dependencies=[Depends(require_permission())])


@router.post("/consent", response_model=ConsentOut, summary="ثبت رضایت بیومتریک (US-108)")
def grant_consent(payload: ConsentIn, db: DbSession, user: CurrentUser):
    return service.grant_consent(db, payload.member_id, payload.policy_version, user=user)


@router.post("/consent/revoke", summary="پس‌گرفتن رضایت + حذف چهره (US-108)")
def revoke_consent(payload: ConsentIn, db: DbSession, user: CurrentUser):
    return service.revoke_consent(db, payload.member_id, user=user)


@router.post("/enroll", response_model=FaceTemplateOut, summary="ثبت چهره (رمزنگاری‌شده)")
def enroll(payload: FaceEnroll, db: DbSession, user: CurrentUser):
    embedding = base64.b64decode(payload.embedding_b64)
    return service.enroll_face(db, payload.member_id, embedding, user=user)


@router.delete("/enroll/{member_id}", summary="حذف قطعی چهره (US-108)")
def delete_face(member_id: int, db: DbSession, user: CurrentUser):
    return service.delete_face(db, member_id, user=user)


@router.post("/checkin", response_model=CheckInOut, summary="چک‌این (US-106)")
def check_in(payload: CheckInIn, db: DbSession, user: CurrentUser):
    return service.check_in(db, payload.member_id, payload.method, user=user)


from modules.face_id.privacy import PRIVACY_NOTICE  # noqa: E402


@router.get("/privacy-notice", summary="متن حریم خصوصی بیومتریک (M31)")
def privacy_notice():
    return PRIVACY_NOTICE


from modules.face_id.deep import lock_status  # noqa: E402


@router.get("/deep-status", summary="وضعیت مدل عمیق چهره (model_lock)")
def deep_status():
    return lock_status()

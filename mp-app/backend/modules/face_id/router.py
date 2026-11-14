"""روتر face_id — رضایت، چهره، چک‌این."""

from __future__ import annotations

import base64

from fastapi import APIRouter

from app.deps import DbSession
from modules.face_id import service
from modules.face_id.schemas import (
    CheckInIn,
    CheckInOut,
    ConsentIn,
    ConsentOut,
    FaceEnroll,
    FaceTemplateOut,
)

router = APIRouter(prefix="/face", tags=["face-id"])


@router.post("/consent", response_model=ConsentOut, summary="ثبت رضایت بیومتریک (US-108)")
def grant_consent(payload: ConsentIn, db: DbSession):
    return service.grant_consent(db, payload.member_id, payload.policy_version)


@router.post("/consent/revoke", summary="پس‌گرفتن رضایت + حذف چهره (US-108)")
def revoke_consent(payload: ConsentIn, db: DbSession):
    return service.revoke_consent(db, payload.member_id)


@router.post("/enroll", response_model=FaceTemplateOut, summary="ثبت چهره (رمزنگاری‌شده)")
def enroll(payload: FaceEnroll, db: DbSession):
    embedding = base64.b64decode(payload.embedding_b64)
    return service.enroll_face(db, payload.member_id, embedding)


@router.delete("/enroll/{member_id}", summary="حذف قطعی چهره (US-108)")
def delete_face(member_id: int, db: DbSession):
    return service.delete_face(db, member_id)


@router.post("/checkin", response_model=CheckInOut, summary="چک‌این (US-106)")
def check_in(payload: CheckInIn, db: DbSession):
    return service.check_in(db, payload.member_id, payload.method)

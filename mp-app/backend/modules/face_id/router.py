"""روتر face_id — رضایت، چهره، چک‌این."""

from __future__ import annotations

import base64

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.deps import CurrentUser, DbSession, require_permission
from modules.face_id import service
from modules.face_id.schemas import (
    CheckInIn,
    CheckInOut,
    CheckInQrIn,
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


# ── چک‌این با QR (M32) — توکن امضاشده، بدون واسط [finn] ──


@router.get("/qr-token", summary="توکن QR چک‌این عضو")
def qr_token(db: DbSession, user: CurrentUser):
    from app.errors import NotFoundError
    from app.security.jwt import create_checkin_qr_token
    from db.models import Member

    member = db.scalar(select(Member).where(Member.user_id == user.id))
    if member is None:
        raise NotFoundError("پروفایل عضو یافت نشد")
    tok = create_checkin_qr_token(member.id)
    return {"payload": tok, "member_id": member.id}


@router.post("/checkin-qr", summary="چک‌این با QR (کیوسک/پذیرش)")
def checkin_qr(payload: CheckInQrIn, db: DbSession, user: CurrentUser):
    from hashlib import sha256

    from sqlalchemy.exc import IntegrityError

    from app.errors import ApiError, NotFoundError
    from app.security.jwt import decode_checkin_qr_token
    from db.models import CheckIn, Member

    try:
        data = decode_checkin_qr_token(payload.payload)
    except Exception as err:
        raise ApiError("توکن QR نامعتبر یا منقضی است", code="qr_invalid") from err

    member_id = int(data["sub"])
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    from app.security.ownership import ensure_member_scope

    # member role may redeem only its own QR; reception can scan a member's QR.
    ensure_member_scope(db, user, member_id)

    # Store only a digest of the random jti, never the signed QR bearer itself.
    jti_hash = sha256(data["jti"].encode("utf-8")).hexdigest()
    if db.scalar(select(CheckIn.id).where(CheckIn.qr_jti_hash == jti_hash)) is not None:
        raise ApiError("این QR قبلاً استفاده شده است", status_code=409, code="qr_replayed")
    try:
        checkin = service.check_in(db, member_id, "qr", user=user, qr_jti_hash=jti_hash)
    except IntegrityError as err:
        # The unique DB index also closes the concurrent-redemption race.
        db.rollback()
        if db.scalar(select(CheckIn.id).where(CheckIn.qr_jti_hash == jti_hash)) is not None:
            raise ApiError(
                "این QR قبلاً استفاده شده است", status_code=409, code="qr_replayed"
            ) from err
        raise
    return {
        "status": checkin.result,
        "method": "qr",
        "member_id": member_id,
        "denial_reason": checkin.denial_reason,
    }


@router.post("/checkins/{checkin_id}/exit", summary="ثبت خروج — طول جلسهٔ حضور (M42-c2)")
def checkin_exit(checkin_id: int, db: DbSession, user: CurrentUser):
    from datetime import UTC, datetime

    from app.errors import ApiError, ForbiddenError, NotFoundError
    from db.models import CheckIn, Member

    ci = db.get(CheckIn, checkin_id)
    if ci is None:
        raise NotFoundError("چک‌این یافت نشد")
    if user.role == "member":
        from sqlalchemy import select

        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if member is None or member.id != ci.member_id:
            raise ForbiddenError("فقط خروج خودتان ثبت می‌شود")
    if ci.checked_out_at is not None:
        raise ApiError("خروج این چک‌این قبلاً ثبت شده", code="already_checked_out")
    ci.checked_out_at = datetime.now(UTC)
    db.commit()
    return {
        "checkin_id": ci.id,
        "member_id": ci.member_id,
        "checked_in_at": ci.created_at.isoformat(),
        "checked_out_at": ci.checked_out_at.isoformat(),
    }

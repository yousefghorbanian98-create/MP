"""روتر auth — OTP و نشست، با rate-limit (slowapi) روی مسیرهای حساس."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.deps import AuthenticatedUser, DbSession
from modules.auth import service
from modules.auth.schemas import (
    LogoutRequest,
    MessageResponse,
    OtpRequest,
    OtpRequestResponse,
    OtpVerify,
    PhoneChangeCode,
    PhoneChangeConfirmResponse,
    PhoneChangeRequest,
    PhoneChangeStepResponse,
    RefreshRequest,
    TokenPair,
)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    # Production shares limits across all Uvicorn workers through Valkey. Local
    # dev/tests stay deterministic and do not require a running cache service.
    storage_uri=settings.valkey_url if settings.environment == "production" else "memory://",
)

router = APIRouter(prefix="/auth", tags=["auth"])


def rate_limit_storage_healthy() -> bool:
    """Readiness probe for SlowAPI's configured backend (Valkey in production)."""
    try:
        return bool(limiter._storage.check())
    except Exception:  # noqa: BLE001 — unavailable storage must not report ready
        return False


@router.post(
    "/otp/request",
    response_model=OtpRequestResponse,
    summary="درخواست کد OTP",
)
@limiter.limit(settings.otp_burst_limit)
@limiter.limit(settings.otp_rate_limit)
def otp_request(payload: OtpRequest, request: Request, db: DbSession):
    return service.request_otp(db, payload.phone)


@router.post("/otp/verify", response_model=TokenPair, summary="تأیید OTP و ورود")
@limiter.limit(settings.otp_burst_limit)
@limiter.limit(settings.otp_rate_limit)
def otp_verify(payload: OtpVerify, request: Request, db: DbSession):
    return service.verify_otp(db, payload.phone, payload.code)


@router.post(
    "/phone-change/request",
    response_model=PhoneChangeStepResponse,
    summary="شروع تغییر شماره پس از نشست معتبر",
)
@limiter.limit(settings.otp_burst_limit)
@limiter.limit(settings.otp_rate_limit)
def phone_change_request(
    payload: PhoneChangeRequest, request: Request, db: DbSession, user: AuthenticatedUser
):
    return service.request_phone_change(db, user, payload.new_phone)


@router.post(
    "/phone-change/verify-old",
    response_model=PhoneChangeStepResponse,
    summary="تأیید شمارهٔ فعلی و ارسال OTP به شمارهٔ جدید",
)
@limiter.limit(settings.otp_burst_limit)
@limiter.limit(settings.otp_rate_limit)
def phone_change_verify_old(
    payload: PhoneChangeCode, request: Request, db: DbSession, user: AuthenticatedUser
):
    return service.verify_old_phone_change_otp(db, user, payload.challenge_id, payload.code)


@router.post(
    "/phone-change/confirm",
    response_model=PhoneChangeConfirmResponse,
    summary="تأیید شمارهٔ جدید و ابطال همهٔ نشست‌ها",
)
@limiter.limit(settings.otp_burst_limit)
@limiter.limit(settings.otp_rate_limit)
def phone_change_confirm(
    payload: PhoneChangeCode, request: Request, db: DbSession, user: AuthenticatedUser
):
    return service.confirm_phone_change(db, user, payload.challenge_id, payload.code)


@router.post("/refresh", response_model=TokenPair, summary="تعویض refresh token")
@limiter.limit(settings.login_rate_limit)
def refresh(payload: RefreshRequest, request: Request, db: DbSession):
    return service.refresh_session(db, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="خروج از نشست فعلی")
def logout(payload: LogoutRequest, db: DbSession):
    return service.logout(db, payload.refresh_token)


@router.get("/sessions", summary="نشست‌های فعال من (دستگاه‌ها)")
def sessions(
    user: AuthenticatedUser,
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
):
    from app.security.jwt import decode_access_token

    sid: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        sid = decode_access_token(authorization.split(" ", 1)[1].strip()).get("sid")
    return service.list_sessions(db, user_id=user.id, current_sid=sid)


@router.delete("/sessions/{session_id}", summary="ابطال یک نشست/دستگاه")
def revoke_session(session_id: int, user: AuthenticatedUser, db: DbSession):
    return service.revoke_session(db, user_id=user.id, session_id=session_id)


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="خروج از همهٔ دستگاه‌ها (US-404)",
)
def logout_all(user: AuthenticatedUser, db: DbSession):
    return service.logout_all(db, user.id)

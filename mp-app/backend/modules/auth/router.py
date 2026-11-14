"""روتر auth — OTP و نشست، با rate-limit (slowapi) روی مسیرهای حساس."""

from __future__ import annotations

from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.deps import CurrentUser, DbSession
from modules.auth import service
from modules.auth.schemas import (
    LogoutRequest,
    MessageResponse,
    OtpRequest,
    OtpRequestResponse,
    OtpVerify,
    RefreshRequest,
    TokenPair,
)

limiter = Limiter(key_func=get_remote_address, default_limits=[])

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/otp/request",
    response_model=OtpRequestResponse,
    summary="درخواست کد OTP",
)
@limiter.limit(settings.otp_rate_limit)
def otp_request(payload: OtpRequest, request: Request, db: DbSession):
    return service.request_otp(db, payload.phone)


@router.post("/otp/verify", response_model=TokenPair, summary="تأیید OTP و ورود")
@limiter.limit(settings.otp_rate_limit)
def otp_verify(payload: OtpVerify, request: Request, db: DbSession):
    return service.verify_otp(db, payload.phone, payload.code)


@router.post("/refresh", response_model=TokenPair, summary="تعویض refresh token")
@limiter.limit(settings.login_rate_limit)
def refresh(payload: RefreshRequest, request: Request, db: DbSession):
    return service.refresh_session(db, payload.refresh_token)


@router.post("/logout", response_model=MessageResponse, summary="خروج از نشست فعلی")
def logout(payload: LogoutRequest, db: DbSession):
    return service.logout(db, payload.refresh_token)


@router.post(
    "/logout-all",
    response_model=MessageResponse,
    summary="خروج از همهٔ دستگاه‌ها (US-404)",
)
def logout_all(user: CurrentUser, db: DbSession):
    return service.logout_all(db, user.id)

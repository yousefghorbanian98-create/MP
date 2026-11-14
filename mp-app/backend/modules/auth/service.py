"""سرویس auth — OTP (فقط هش)، نشست JWT، refresh قابل ابطال."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import ApiError, UnauthorizedError
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from db.models import OtpCode, RefreshToken, User

# هش OTP با salt تصادفی — هرگز خام ذخیره نمی‌شود (R-002)
_SALT_PREFIX = "mp-otp"


def _hash_otp(code: str, salt: str) -> str:
    return hashlib.sha256(f"{_SALT_PREFIX}:{salt}:{code}".encode()).hexdigest()


def request_otp(db: Session, phone: str) -> dict:
    """ارسال OTP — کد تولید و هش‌شده ذخیره می‌شود؛ ارسال پیامک از provider (جای‌پر)."""
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(8)
    otp = OtpCode(
        phone=phone,
        code_hash=f"{salt}${_hash_otp(code, salt)}",
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.otp_ttl_seconds),
    )
    db.add(otp)
    db.commit()
    # ارسال واقعی پیامک در M13/M15 (provider) — خروجی dev فقط لاگ ساختاریافته است
    from app.sms import get_sms_provider

    provider = get_sms_provider()
    sent = provider.send(phone, f"کد تایید MuscleParadise: {code}")
    if not sent:
        from app.errors import ApiError

        raise ApiError("ارسال پیامک ناموفق بود؛ دوباره تلاش کنید", code="sms_failed")
    out = {"phone": phone, "expires_in": settings.otp_ttl_seconds}
    if provider.name == "dev":
        out["dev_code"] = code  # فقط در حالت توسعه
    return out


def verify_otp(db: Session, phone: str, code: str) -> dict:
    """تأیید OTP و ورود — کاربر جدید می‌سازد (عضو)، توکن صادر می‌کند."""
    otp = db.scalar(
        select(OtpCode)
        .where(OtpCode.phone == phone, OtpCode.used.is_(False))
        .order_by(OtpCode.id.desc())
        .limit(1)
    )
    if otp is None:
        raise UnauthorizedError("کدی برای این شماره درخواست نشده است")
    if otp.attempts >= settings.otp_max_attempts:
        raise ApiError("تعداد تلاش‌ها تمام شد؛ کد جدید بگیرید", code="otp_locked")
    otp.attempts += 1
    if datetime.now(UTC) > _aware(otp.expires_at):
        db.commit()
        raise UnauthorizedError("کد منقضی شده است")
    salt, _, stored = otp.code_hash.partition("$")
    if not hmac.compare_digest(_hash_otp(code, salt), stored):
        db.commit()
        raise UnauthorizedError("کد نادرست است")
    otp.used = True
    user = db.scalar(select(User).where(User.phone == phone))
    if user is None:
        user = User(phone=phone, full_name="", role="member")
        db.add(user)
        db.flush()
    access = create_access_token(user.id, user.role)
    refresh, refresh_hash, expires = create_refresh_token()
    db.add(
        RefreshToken(user_id=user.id, token_hash=refresh_hash, expires_at=expires, device_info="")
    )
    db.commit()
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "phone": user.phone,
            "role": user.role,
            "full_name": user.full_name,
        },
    }


def refresh_session(db: Session, refresh_token: str) -> dict:
    """تعویض refresh — rotation: توکن قبلی باطل و توکن جدید صادر می‌شود."""
    token_hash = hash_token(refresh_token)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    now = datetime.now(UTC)
    if row is None or row.revoked_at is not None or now > _aware(row.expires_at):
        raise UnauthorizedError("refresh token نامعتبر است")
    row.revoked_at = now
    user = db.get(User, row.user_id)
    if (
        # nosemgrep-next-line: ستون SQLAlchemy (Mapped[bool]) است نه فراخوانی تابع
        user is None or not user.is_active  # nosemgrep
    ):
        raise UnauthorizedError("کاربر فعال نیست")
    access = create_access_token(user.id, user.role)
    new_refresh, new_hash, expires = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=new_hash, expires_at=expires))
    db.commit()
    return {"access_token": access, "refresh_token": new_refresh, "token_type": "bearer"}


def logout(db: Session, refresh_token: str) -> dict:
    token_hash = hash_token(refresh_token)
    row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    if row is not None and row.revoked_at is None:
        row.revoked_at = datetime.now(UTC)
        db.commit()
    return {"status": "logged_out"}


def logout_all(db: Session, user_id: int) -> dict:
    """«خروج از همهٔ دستگاه‌ها» — ابطال همهٔ refreshها (US-404)."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    db.commit()
    from modules.admin.service import audit

    audit(db, user_id, "logout_all", "user", user_id, {})
    return {"status": "all_sessions_revoked"}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

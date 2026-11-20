"""سرویس auth — OTP (فقط هش)، نشست JWT، refresh قابل ابطال."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import ApiError, ConflictError, NotFoundError, UnauthorizedError
from app.security.jwt import (
    create_access_token,
    create_refresh_token,
    hash_token,
)
from db.models import OtpCode, PhoneChangeChallenge, RefreshToken, User

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
    # فاز ۴: حساب غیرفعال نباید حتی نشست بگیرد. پیش از این، توکن صادر می‌شد و
    # فقط درخواست بعدی ۴۰۱ می‌گرفت — یعنی ورودِ موفق به حساب بسته‌شده.
    # کد مصرف‌شده ثبت می‌شود تا با همان کد دوباره تلاش نشود.
    if not user.is_active:  # nosemgrep: ستون SQLAlchemy است نه فراخوانی تابع
        db.commit()
        raise UnauthorizedError("کاربر فعال نیست")
    refresh, refresh_hash, expires = create_refresh_token()
    access = create_access_token(
        user.id, user.role, session_id=refresh_hash, auth_version=user.auth_version
    )
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
    new_refresh, new_hash, expires = create_refresh_token()
    access = create_access_token(
        user.id, user.role, session_id=new_hash, auth_version=user.auth_version
    )
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


def _phone_change_code() -> tuple[str, str]:
    code = f"{secrets.randbelow(1_000_000):06d}"
    salt = secrets.token_hex(16)
    return code, f"{salt}${_hash_otp(code, salt)}"


def _matches_otp_hash(code: str, stored_hash: str) -> bool:
    salt, separator, digest = stored_hash.partition("$")
    return bool(separator and salt and digest) and hmac.compare_digest(
        _hash_otp(code, salt), digest
    )


def _phone_change_challenge(db: Session, user: User, challenge_id: str) -> PhoneChangeChallenge:
    challenge = db.scalar(
        select(PhoneChangeChallenge).where(
            PhoneChangeChallenge.challenge_id == challenge_id,
            PhoneChangeChallenge.user_id == user.id,
        )
    )
    if (
        challenge is None
        or challenge.completed_at is not None
        or challenge.invalidated_at is not None
    ):
        raise NotFoundError("درخواست تغییر شماره معتبر نیست")

    now = datetime.now(UTC)
    if now >= _aware(challenge.expires_at):
        challenge.invalidated_at = now
        db.commit()
        raise ApiError(
            "درخواست تغییر شماره منقضی شده است", status_code=410, code="phone_change_expired"
        )
    if user.phone != challenge.old_phone:
        challenge.invalidated_at = now
        db.commit()
        raise ConflictError("شمارهٔ حساب از زمان درخواست تغییر کرده است")
    return challenge


def _deliver_phone_change_code(
    db: Session,
    challenge: PhoneChangeChallenge,
    phone: str,
    code: str,
    stage: str,
) -> dict:
    from app.sms import get_sms_provider

    provider = get_sms_provider()
    try:
        sent = provider.send(phone, f"کد تغییر شماره برای تأیید {stage} MuscleParadise: {code}")
    except Exception:
        sent = False
    if not sent:
        challenge.invalidated_at = datetime.now(UTC)
        db.commit()
        raise ApiError("ارسال پیامک ناموفق بود؛ فرایند را دوباره آغاز کنید", code="sms_failed")

    result = {"challenge_id": challenge.challenge_id, "expires_in": settings.otp_ttl_seconds}
    if provider.name == "dev":
        result["dev_code"] = code
    return result


def request_phone_change(db: Session, user: User, new_phone: str) -> dict:
    """Start phone change by sending a challenge code only to the current phone."""
    if new_phone == user.phone:
        raise ApiError(
            "شمارهٔ جدید با شمارهٔ فعلی یکسان است", status_code=409, code="phone_unchanged"
        )
    if db.scalar(select(User.id).where(User.phone == new_phone)) is not None:
        raise ApiError(
            "این شماره قبلاً به حساب دیگری متصل است", status_code=409, code="phone_in_use"
        )

    now = datetime.now(UTC)
    db.execute(
        update(PhoneChangeChallenge)
        .where(
            PhoneChangeChallenge.user_id == user.id,
            PhoneChangeChallenge.completed_at.is_(None),
            PhoneChangeChallenge.invalidated_at.is_(None),
        )
        .values(invalidated_at=now)
    )
    code, code_hash = _phone_change_code()
    challenge = PhoneChangeChallenge(
        challenge_id=secrets.token_urlsafe(32),
        user_id=user.id,
        old_phone=user.phone,
        new_phone=new_phone,
        old_code_hash=code_hash,
        expires_at=now + timedelta(seconds=settings.otp_ttl_seconds),
    )
    db.add(challenge)
    db.commit()
    return _deliver_phone_change_code(db, challenge, user.phone, code, "شمارهٔ فعلی")


def verify_old_phone_change_otp(db: Session, user: User, challenge_id: str, code: str) -> dict:
    """Verify the current phone, then send a separate OTP to the proposed number."""
    challenge = _phone_change_challenge(db, user, challenge_id)
    if challenge.old_verified_at is not None:
        raise ConflictError("شمارهٔ فعلی این درخواست قبلاً تأیید شده است")

    now = datetime.now(UTC)
    if challenge.old_attempts >= settings.otp_max_attempts:
        challenge.invalidated_at = now
        db.commit()
        raise ApiError(
            "تعداد تلاش‌ها تمام شد؛ فرایند را دوباره آغاز کنید",
            status_code=429,
            code="otp_locked",
        )

    challenge.old_attempts += 1
    if not _matches_otp_hash(code, challenge.old_code_hash):
        locked = challenge.old_attempts >= settings.otp_max_attempts
        if locked:
            challenge.invalidated_at = now
        db.commit()
        if locked:
            raise ApiError(
                "تعداد تلاش‌ها تمام شد؛ فرایند را دوباره آغاز کنید",
                status_code=429,
                code="otp_locked",
            )
        raise ApiError("کد شمارهٔ فعلی نادرست است", code="invalid_otp")

    new_code, new_code_hash = _phone_change_code()
    challenge.old_verified_at = now
    challenge.new_code_hash = new_code_hash
    challenge.expires_at = now + timedelta(seconds=settings.otp_ttl_seconds)
    db.commit()
    return _deliver_phone_change_code(db, challenge, challenge.new_phone, new_code, "شمارهٔ جدید")


def confirm_phone_change(db: Session, user: User, challenge_id: str, code: str) -> dict:
    """Verify the proposed phone, change the unique login number, revoke all sessions."""
    challenge = _phone_change_challenge(db, user, challenge_id)
    if challenge.old_verified_at is None or challenge.new_code_hash is None:
        raise ConflictError("ابتدا شمارهٔ فعلی را تأیید کنید")

    now = datetime.now(UTC)
    if challenge.new_attempts >= settings.otp_max_attempts:
        challenge.invalidated_at = now
        db.commit()
        raise ApiError(
            "تعداد تلاش‌ها تمام شد؛ فرایند را دوباره آغاز کنید",
            status_code=429,
            code="otp_locked",
        )

    challenge.new_attempts += 1
    if not _matches_otp_hash(code, challenge.new_code_hash):
        locked = challenge.new_attempts >= settings.otp_max_attempts
        if locked:
            challenge.invalidated_at = now
        db.commit()
        if locked:
            raise ApiError(
                "تعداد تلاش‌ها تمام شد؛ فرایند را دوباره آغاز کنید",
                status_code=429,
                code="otp_locked",
            )
        raise ApiError("کد شمارهٔ جدید نادرست است", code="invalid_otp")

    duplicate = db.scalar(
        select(User.id).where(User.phone == challenge.new_phone, User.id != user.id)
    )
    if duplicate is not None:
        challenge.invalidated_at = now
        db.commit()
        raise ApiError(
            "این شماره قبلاً به حساب دیگری متصل است", status_code=409, code="phone_in_use"
        )

    try:
        changed = db.execute(
            update(User)
            .where(User.id == user.id, User.phone == challenge.old_phone)
            .values(phone=challenge.new_phone, auth_version=User.auth_version + 1)
        )
        if changed.rowcount != 1:
            challenge.invalidated_at = now
            db.commit()
            raise ConflictError("شمارهٔ حساب هم‌زمان تغییر کرده است؛ دوباره وارد شوید")

        challenge.completed_at = now
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=now)
        )
        db.commit()
    except IntegrityError as exc:
        # A competing account may claim the number after the preflight SELECT.
        # SQLite/PostgreSQL can raise the unique violation at UPDATE execution,
        # not only at commit, so both operations must be inside this handler.
        db.rollback()
        duplicate = db.scalar(
            select(User.id).where(User.phone == challenge.new_phone, User.id != user.id)
        )
        if duplicate is None:
            raise
        current = db.get(PhoneChangeChallenge, challenge_id)
        if current is not None and current.completed_at is None:
            current.invalidated_at = datetime.now(UTC)
            db.commit()
        raise ApiError(
            "این شماره قبلاً به حساب دیگری متصل است", status_code=409, code="phone_in_use"
        ) from exc

    return {"status": "phone_changed", "phone": challenge.new_phone}


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)

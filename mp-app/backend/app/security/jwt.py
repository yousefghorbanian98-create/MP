"""توکن‌های JWT — access کوتاه‌عمر + refresh بلند (قابل ابطال در DB)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

import jwt as pyjwt
from jwt import PyJWTError as JWTError

from app.config import settings
from app.errors import UnauthorizedError

ALGORITHM = "HS256"


def create_access_token(
    user_id: int,
    role: str,
    session_id: str | None = None,
    auth_version: int | None = None,
) -> str:
    """Issue an access JWT bound to its refresh row and user auth-version when supplied."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    if session_id is not None:
        payload["sid"] = session_id
    if auth_version is not None:
        payload["ver"] = auth_version
    return pyjwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_checkin_qr_token(member_id: int) -> str:
    """توکن QR کوتاه‌عمر و جدا از bearer access token؛ یک jti مستقل برای replay gate."""
    if member_id < 1:
        raise ValueError("member_id must be positive")
    now = datetime.now(UTC)
    return pyjwt.encode(
        {
            "sub": str(member_id),
            "type": "checkin_qr",
            "jti": secrets.token_urlsafe(32),
            "iat": now,
            "exp": now + timedelta(minutes=2),
        },
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def decode_checkin_qr_token(token: str) -> dict:
    """اعتبارسنجی claims توکن QR؛ هرگز آن را به‌عنوان access token تفسیر نکن."""
    try:
        payload = pyjwt.decode(
            token,
            settings.secret_key,
            algorithms=[ALGORITHM],
            options={"require": ["sub", "type", "jti", "iat", "exp"]},
        )
    except JWTError as exc:
        raise UnauthorizedError("توکن QR نامعتبر یا منقضی است") from exc
    if payload.get("type") != "checkin_qr":
        raise UnauthorizedError("نوع توکن QR نادرست است")
    subject = payload.get("sub")
    jti = payload.get("jti")
    if (
        not isinstance(subject, str)
        or not subject.isdecimal()
        or int(subject) < 1
        or not isinstance(jti, str)
        or len(jti) < 32
        or len(jti) > 128
    ):
        raise UnauthorizedError("claims توکن QR نامعتبر است")
    return payload


def create_refresh_token() -> tuple[str, str, datetime]:
    """(توکن خام، هش توکن، تاریخ انقضا) — خام فقط یک‌بار به کاربر برمی‌گردد."""
    token = secrets.token_urlsafe(48)
    expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    return token, hash_token(token), expires


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict:
    try:
        payload = pyjwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("توکن نامعتبر یا منقضی است") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("نوع توکن نادرست است")
    return payload

"""توکن‌های JWT — access کوتاه‌عمر + refresh بلند (قابل ابطال در DB)."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.config import settings
from app.errors import UnauthorizedError

ALGORITHM = "HS256"


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token() -> tuple[str, str, datetime]:
    """(توکن خام، هش توکن، تاریخ انقضا) — خام فقط یک‌بار به کاربر برمی‌گردد."""
    token = secrets.token_urlsafe(48)
    expires = datetime.now(UTC) + timedelta(days=settings.refresh_token_days)
    return token, hash_token(token), expires


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise UnauthorizedError("توکن نامعتبر یا منقضی است") from exc
    if payload.get("type") != "access":
        raise UnauthorizedError("نوع توکن نادرست است")
    return payload

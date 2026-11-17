"""وابستگی‌های مشترک FastAPI — session دیتابیس، کاربر جاری، نقش."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Header, Path, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ForbiddenError, UnauthorizedError
from db.base import get_session_factory
from db.models import RefreshToken, User


def get_db() -> Generator[Session, None, None]:
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]

# شناسه‌های مسیر با سقف — نه `int` خالی.
#
# یافتهٔ DAST (M60/R18): `int` خالی در FastAPI هر عدد صحیح ۶۴بیتی و بزرگ‌تر را
# می‌پذیرد؛ SQLite برای `10**30` استثنای `OverflowError` می‌دهد و نتیجه ۵۰۰ بود
# (روی مسیرهایی مثل `/assessments/limb/member/{member_id}/report`). با سقف،
# FastAPI پیش از رسیدن به لایهٔ داده ۴۲۲ می‌دهد. سقف ۲^۵۳ است تا با JSON
# جاوااسکریپت (Number.MAX_SAFE_INTEGER) و کلاینت فلاتر هم‌خوان بماند.
MAX_SAFE_ID = 9_007_199_254_740_991

# در امضای تابع wrapper است تا هر سه‌جای `SafeId` یک رفتار داشته باشد.
PathId = Annotated[int, Path(ge=1, le=MAX_SAFE_ID)]


def get_current_user(
    db: DbSession,
    authorization: Annotated[str | None, Header()] = None,
):
    """کاربر جاری از header `Authorization: Bearer <access>`."""
    from app.security.jwt import decode_access_token

    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError()
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user = db.get(User, int(payload["sub"]))
    if (
        # nosemgrep-next-line: پراپرتی SQLAlchemy (Mapped[bool]) است نه فراخوانی تابع
        user is None or not user.is_active  # nosemgrep
    ):
        raise UnauthorizedError("کاربر فعال نیست")

    # A per-user version change revokes even legacy JWTs that predate `sid`.
    # Versionless tokens remain compatible until the account explicitly bumps
    # its version (phone change); after that, only tokens carrying the new
    # version are accepted.
    auth_version = payload.get("ver")
    if auth_version is None:
        if user.auth_version != 0:
            raise UnauthorizedError("نشست معتبر نیست")
    elif (
        not isinstance(auth_version, int)
        or isinstance(auth_version, bool)
        or auth_version != user.auth_version
    ):
        raise UnauthorizedError("نشست معتبر نیست")

    # New OTP access tokens are bound to the hashed refresh-token row. Rotating
    # or logging out that refresh session then revokes its access JWTs as well.
    # Tokens without `sid` are kept temporarily compatible with older callers;
    # they remain stateless until their short access-token expiry.
    session_id = payload.get("sid")
    if session_id is not None:
        if not isinstance(session_id, str) or not session_id:
            raise UnauthorizedError("نشست معتبر نیست")
        session = db.scalar(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.token_hash == session_id,
            )
        )
        if session is None or session.revoked_at is not None:
            raise UnauthorizedError("نشست معتبر نیست")
        expires_at = session.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at <= datetime.now(UTC):
            raise UnauthorizedError("نشست معتبر نیست")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_authenticated(user: CurrentUser) -> User:
    """Explicit auth-only guard for endpoints that allow every role."""
    return user


require_authenticated.__rbac__ = "authenticated"  # type: ignore[attr-defined]
AuthenticatedUser = Annotated[User, Depends(require_authenticated)]


def require_roles(*roles: str):
    """guard نقش ساده — فقط نقش‌های مشخص‌شده (compat).

    `super_admin` (مالک سیستم) همیشه مجاز است — هم‌راستا با سیاست casbin
    («super_admin، همه‌چیز») — باگ REA-2026-11-15: قفل شدن مالک از مسیرهای require_roles.
    """

    def _guard(user: CurrentUser) -> User:
        if user.role not in roles and user.role != "super_admin":
            raise ForbiddenError(f"نقش {user.role} مجاز نیست")
        return user

    # برچسب برای گیتِ «هر مسیر یک guard دارد» (tests/integration/test_route_guards.py):
    # بدون برچسب، گیت نمی‌تواند guardهای همین ماژول را از تابع‌های عادی تفکیک کند.
    _guard.__rbac__ = "roles"  # type: ignore[attr-defined]
    return _guard


def require_permission():
    """guard مجوز با casbin (M08) — نقش کاربر + مسیر/متد درخواست."""

    def _guard(user: CurrentUser, request: Request) -> User:
        from security.rbac import enforce

        if not enforce(user.role, request.url.path, request.method):
            raise ForbiddenError(
                f"نقش {user.role} برای {request.method} {request.url.path} مجاز نیست"
            )
        return user

    _guard.__rbac__ = "permission"  # type: ignore[attr-defined]
    return _guard

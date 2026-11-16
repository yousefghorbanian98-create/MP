"""وابستگی‌های مشترک FastAPI — session دیتابیس، کاربر جاری، نقش."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, Path, Request
from sqlalchemy.orm import Session

from app.errors import ForbiddenError, UnauthorizedError
from db.base import get_session_factory
from db.models import User


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
    from db.models import User

    user = db.get(User, int(payload["sub"]))
    if (
        # nosemgrep-next-line: پراپرتی SQLAlchemy (Mapped[bool]) است نه فراخوانی تابع
        user is None or not user.is_active  # nosemgrep
    ):
        raise UnauthorizedError("کاربر فعال نیست")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


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

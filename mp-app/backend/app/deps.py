"""وابستگی‌های مشترک FastAPI — session دیتابیس، کاربر جاری، نقش."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Header, Request
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
    if user is None or not user.is_active:  # nosemgrep: python.lang.maintainability.is-function-without-parentheses — پراپرتی SQLAlchemy است نه فراخوانی
        raise UnauthorizedError("کاربر فعال نیست")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_roles(*roles: str):
    """guard نقش ساده — فقط نقش‌های مشخص‌شده (compat)."""

    def _guard(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"نقش {user.role} مجاز نیست")
        return user

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

    return _guard

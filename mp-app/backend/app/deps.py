"""وابستگی‌های مشترک FastAPI — session دیتابیس، کاربر جاری، نقش."""

from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.errors import ForbiddenError, UnauthorizedError
from db.base import get_session_factory

if TYPE_CHECKING:
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
    if user is None or not user.is_active:
        raise UnauthorizedError("کاربر فعال نیست")
    return user


CurrentUser = Annotated["User", Depends(get_current_user)]


def require_roles(*roles: str):
    """guard نقش (RBAC کامل با casbin در M08)."""

    def _guard(user: CurrentUser) -> User:
        if user.role not in roles:
            raise ForbiddenError(f"نقش {user.role} مجاز نیست")
        return user

    return _guard

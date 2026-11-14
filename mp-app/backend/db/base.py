"""پایهٔ SQLAlchemy — engine/session/Base برای کل بک‌اند.

ADR-002: از SQLAlchemy 2.x (سبک Mapped/mapped_column) استفاده می‌شود؛
URL دیتابیس از config خوانده می‌شود تا مهاجرت SQLite→Postgres بدون تغییر کد باشد.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """کلاس پایهٔ همهٔ مدل‌ها."""


class TimestampMixin:
    """ستون‌های زمانی مشترک."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BranchMixin:
    """branch_id از روز اول در همهٔ جدول‌های اصلی (لایهٔ ۳ — دام «فراموشی branch_id»)."""

    branch_id: Mapped[int] = mapped_column(nullable=False, index=True, default=1)


_engine = None
_SessionLocal = None


def get_engine(url: str | None = None):
    """ساخت/بازگرداندن engine (برای تست‌ها URL جدا داده می‌شود)."""
    global _engine
    if url is not None:
        return create_engine(url, connect_args={"check_same_thread": False})
    if _engine is None:
        _engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
    return _engine


def get_session_factory(url: str | None = None):
    """سازندهٔ session."""
    global _SessionLocal
    if url is not None:
        return sessionmaker(bind=get_engine(url), autoflush=False, expire_on_commit=False)
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SessionLocal


def init_db(url: str | None = None) -> None:
    """ساخت همهٔ جدول‌ها (فقط برای محیط dev/test — production از Alembic)."""
    from db import models  # noqa: F401  (import برای ثبت مدل‌ها روی Base)

    Base.metadata.create_all(bind=get_engine(url))

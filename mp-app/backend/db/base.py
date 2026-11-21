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


# M46-c4 — پیکربندی استخر اتصال.
#
# زیر بار واقعی (۴۰۰ کاربر همزمان) این خطا رخ داد:
#   QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
# دلیل: FastAPI برای endpointهای sync تا ۴۰ ترد anyio می‌دهد، ولی استخر پیش‌فرض
# SQLAlchemy فقط ۵+۱۰ اتصال دارد. نتیجه صف ۳۰ ثانیه‌ای و ۵۰۰ به‌جای خطای سریع.
#
# انتخاب‌ها:
#   pool_size=10, max_overflow=30  → ظرفیت ۴۰ = دقیقاً تعداد تردها
#   pool_timeout=10                → خرابی سریع و صریح، نه هنگ ۳۰ ثانیه‌ای
#   pool_pre_ping=True             → اتصال مرده بازیابی می‌شود، نه ۵۰۰
#   pool_recycle=1800              → جلوگیری از قطع اتصال توسط proxy/DB
# M48-c2 — بازبینی بعد از افزودن endpoint حجم:
#   با ۱۰+۳۰ ظرفیت، زیر ۳۰۰ کاربر همزمان این خطا در لاگ ظاهر شد:
#     QueuePool limit of size 10 overflow 30 reached, connection timed out
#   و p50 از ۴ms به ۱۹۰ms رفت (صف، نه کندی کد — محاسبه ۱ms است).
# anyio پیش‌فرض ۴۰ ترد برای endpointهای sync می‌دهد؛ ۴۰+۲۰ ظرفیت حاشیهٔ
# امن می‌دهد و `pool_timeout` کوتاه‌تر (۵s) خطا را سریع نشان می‌دهد، نه
# اینکه درخواست ۱۰ ثانیه معلق بماند.
_POOL_SIZE = 40
_MAX_OVERFLOW = 20
_POOL_TIMEOUT = 5
_POOL_RECYCLE = 1800


def _engine_options(url: str) -> dict:
    """گزینه‌های engine بر اساس نوع دیتابیس.

    SQLite در حافظه/فایل از QueuePool استفاده می‌کند ولی `pool_recycle` لازم
    ندارد؛ برای Postgres (مسیر مهاجرت) هر چهار گزینه معنا دارند.
    """
    opts: dict = {
        "connect_args": {"check_same_thread": False},
        "pool_size": _POOL_SIZE,
        "max_overflow": _MAX_OVERFLOW,
        "pool_timeout": _POOL_TIMEOUT,
        "pool_pre_ping": True,
        "pool_recycle": _POOL_RECYCLE,
    }
    if url.startswith("sqlite") and ":memory:" not in url:
        # M46-c4 — SQLite در حالت پیش‌فرض (journal) نوشتن را کامل سریال می‌کند.
        # زیر ۴۰۰ کاربر، تردهای نویسنده پشت قفل می‌مانند، اتصال‌ها برنمی‌گردند و
        # استخر خالی می‌شود ⇒ QueuePool limit reached ⇒ ۵۰۰ و هنگ.
        #   WAL    : خواندن و نوشتن هم‌زمان ممکن می‌شود (پیش‌فرض برای SQLite مدرن)
        #   busy_timeout: به‌جای خطای فوری «database is locked»، انتظار کوتاه
        #   synchronous=NORMAL: با WAL ایمن است و نوشتن را چند برابر سریع‌تر می‌کند
        opts["connect_args"] = {
            "check_same_thread": False,
            "timeout": 15,
        }
        opts["_sqlite_pragmas"] = True

    if url.startswith("sqlite") and ":memory:" in url:
        # استخر ثابت برای DB درون‌حافظه — همه تردها باید یک اتصال ببینند
        from sqlalchemy.pool import StaticPool

        opts["poolclass"] = StaticPool
        for k in ("pool_size", "max_overflow", "pool_timeout", "pool_recycle"):
            opts.pop(k, None)
    return opts


def _apply_sqlite_pragmas(engine) -> None:
    """WAL + busy_timeout برای هر اتصال جدید (M46-c4).

    بدون این، نوشتن‌های همزمان قفل کامل می‌گیرند و استخر اتصال خالی می‌شود.
    """
    from sqlalchemy import event

    if engine.dialect.name != "sqlite":
        return

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_conn, _record):
        cur = dbapi_conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.execute("PRAGMA busy_timeout=15000")
            cur.execute("PRAGMA foreign_keys=ON")
        finally:
            cur.close()


def _build_engine(url: str):
    opts = _engine_options(url)
    wants_pragmas = opts.pop("_sqlite_pragmas", False)
    engine = create_engine(url, **opts)
    if wants_pragmas:
        _apply_sqlite_pragmas(engine)
    return engine


def get_engine(url: str | None = None):
    """ساخت/بازگرداندن engine (برای تست‌ها URL جدا داده می‌شود)."""
    global _engine
    if url is not None:
        return _build_engine(url)
    if _engine is None:
        _engine = _build_engine(settings.database_url)
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


def reset_engine() -> None:
    """بازنشانی engine/session سراسری (برای تست‌ها)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None

"""M46-c4 — پیکربندی استخر اتصال (باگ واقعیِ کشف‌شده زیر بار).

زیر ۴۰۰ کاربر همزمان، `QueuePool limit of size 5 overflow 10 reached` رخ داد:
FastAPI برای endpointهای sync تا ۴۰ ترد همزمان می‌دهد، ولی استخر فقط ۱۵ اتصال
داشت. نتیجه: صف ۳۰ ثانیه‌ای و پاسخ‌های ۵۰۰ به‌جای خطای سریع.

این تست قفل می‌کند که:
  * ظرفیت استخر ≥ تعداد تردهای پیش‌فرض anyio (۴۰)
  * timeout کوتاه است تا خرابی سریع و صریح باشد، نه هنگ
"""

from __future__ import annotations

import pytest

from app.config import settings


@pytest.fixture()
def fresh_engine(tmp_path, monkeypatch):
    from db.base import get_engine, reset_engine

    reset_engine()
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/pool.db")
    eng = get_engine()
    yield eng
    eng.dispose()
    reset_engine()


def test_pool_capacity_covers_threadpool(fresh_engine) -> None:
    pool = fresh_engine.pool
    capacity = pool.size() + pool._max_overflow  # noqa: SLF001 — عدد پیکربندی، نه رفتار
    assert capacity >= 40, (
        f"ظرفیت استخر {capacity} کمتر از ۴۰ ترد anyio است؛ زیر بار همان "
        "QueuePool limit ... reached رخ می‌دهد"
    )


def test_pool_timeout_is_short_so_failures_are_fast(fresh_engine) -> None:
    assert fresh_engine.pool._timeout <= 15, "timeout بلند یعنی درخواست‌ها به‌جای خطا هنگ می‌کنند"


def test_pool_pre_ping_enabled(fresh_engine) -> None:
    """اتصال مرده باید پیش از استفاده بازیابی شود، نه اینکه ۵۰۰ بدهد."""
    assert fresh_engine.pool._pre_ping is True


def test_sqlite_wal_and_busy_timeout_enabled(tmp_path, monkeypatch) -> None:
    """M46-c4 — بدون WAL، نوشتن‌های همزمان قفل کامل می‌گیرند و استخر خالی می‌شود."""
    from db.base import get_engine, reset_engine

    reset_engine()
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/wal.db")
    eng = get_engine()
    with eng.connect() as c:
        assert c.exec_driver_sql("PRAGMA journal_mode").scalar().lower() == "wal"
        assert c.exec_driver_sql("PRAGMA busy_timeout").scalar() >= 5000
        assert c.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1
    eng.dispose()
    reset_engine()

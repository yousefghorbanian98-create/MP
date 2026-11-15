"""M47-c1 — قفل‌کردن «schema = مدل».

پیش از این، `alembic check` روی DB تمیز ۱۴ عملیات drift گزارش می‌کرد:
۱۰ ایندکس گم‌شده + ۴ ستون nullable که مدل NOT NULL می‌خواست.

این تست همان چیزی را چک می‌کند که در استقرار خطا می‌داد، بدون نیاز به
اجرای دستی alembic:
  * مهاجرت‌ها روی DB خالی اجرا می‌شوند (هیچ‌کدام شکست نمی‌خورد)
  * نتیجه دقیقاً با مدل‌ها هم‌خوان است (صفر drift)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def _alembic(db_url: str, *args: str) -> subprocess.CompletedProcess:
    import os

    env = {**os.environ, "MP_DATABASE_URL": db_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )


def test_migrations_produce_no_drift(tmp_path) -> None:
    db_url = f"sqlite:///{tmp_path}/drift.db"

    up = _alembic(db_url, "upgrade", "head")
    assert up.returncode == 0, f"upgrade شکست خورد:\n{up.stderr[-2000:]}"

    check = _alembic(db_url, "check")
    combined = check.stdout + check.stderr
    assert "No new upgrade operations detected" in combined, (
        "schema با مدل‌ها هم‌خوان نیست — drift باقی مانده:\n" + combined[-2000:]
    )


def test_migration_round_trip(tmp_path) -> None:
    """downgrade باید کار کند — مهاجرتی که برگشت‌پذیر نیست، در استقرار تله است."""
    db_url = f"sqlite:///{tmp_path}/roundtrip.db"

    assert _alembic(db_url, "upgrade", "head").returncode == 0
    down = _alembic(db_url, "downgrade", "-1")
    assert down.returncode == 0, f"downgrade شکست خورد:\n{down.stderr[-2000:]}"
    assert _alembic(db_url, "upgrade", "head").returncode == 0

    check = _alembic(db_url, "check")
    assert "No new upgrade operations detected" in (check.stdout + check.stderr)


def test_class_booking_timestamps_not_redefined() -> None:
    """M47-c1 — بازتعریف created_at در ClassBooking، index=True را از mixin می‌گرفت."""
    from db.models import ClassBooking

    assert ClassBooking.__table__.c.created_at.index is True
    # updated_at طبق TimestampMixin ایندکس نمی‌شود
    assert ClassBooking.__table__.c.updated_at.index is None

"""تست یکپارچگی Alembic — migration از صفر تا آخر روی دیتابیس تمیز (گیت M03)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _alembic(args: list[str], db_path: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, MP_DATABASE_URL=f"sqlite:///{db_path}")
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_upgrade_from_zero(tmp_path):
    db = tmp_path / "fresh.db"
    result = _alembic(["upgrade", "head"], db)
    assert result.returncode == 0, result.stderr
    assert db.exists()


def test_upgrade_downgrade_upgrade(tmp_path):
    db = tmp_path / "cycle.db"
    assert _alembic(["upgrade", "head"], db).returncode == 0
    assert _alembic(["downgrade", "base"], db).returncode == 0
    assert _alembic(["upgrade", "head"], db).returncode == 0


def test_schema_has_core_tables(tmp_path):
    import sqlite3

    db = tmp_path / "schema.db"
    assert _alembic(["upgrade", "head"], db).returncode == 0
    con = sqlite3.connect(db)
    tables = {r[0] for r in con.execute("select name from sqlite_master where type='table'")}
    con.close()
    for t in ["users", "members", "payments", "checkins", "face_templates", "workout_programs"]:
        assert t in tables, f"جدول {t} در migration نیست"

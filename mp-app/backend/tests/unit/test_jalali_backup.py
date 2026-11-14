"""تست‌های تبدیل جلالی و بکاپ/بازیابی (M23-c2)."""

from __future__ import annotations

import sqlite3
from datetime import date
from pathlib import Path

from app.jalali import format_jalali, to_gregorian, to_jalali
from scripts.backup import backup, restore


def test_jalali_roundtrip_known_dates() -> None:
    # نوروز ۱۴۰۵ = ۲۰۲۶-۰۳-۲۱
    assert to_jalali(2026, 3, 21) == (1405, 1, 1)
    assert to_gregorian(1405, 1, 1) == (2026, 3, 21)
    # نمونه‌های بیشتر: رفت‌وبرگشت باید پایدار باشد
    for g in [(2026, 11, 14), (2024, 2, 29), (2000, 1, 1), (1999, 12, 31)]:
        j = to_jalali(*g)
        assert to_gregorian(*j) == g


def test_format_jalali_display_only() -> None:
    s = format_jalali(date(2026, 3, 21))
    assert "فروردین" in s and "۱۴۰۵" in s or "1405" in s


def test_backup_restore_roundtrip(tmp_path: Path) -> None:
    # دیتابیس نمونه با یک جدول
    db = tmp_path / "mp.db"
    conn = sqlite3.connect(db)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()
    archive = backup(tmp_path / "out", db)
    assert archive.exists()
    # خراب‌سازی دیتابیس و بازیابی
    db.write_bytes(b"corrupt")
    manifest = restore(archive, db)
    assert "mp.db" in manifest["files"]
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT x FROM t").fetchone()[0] == 42
    conn.close()

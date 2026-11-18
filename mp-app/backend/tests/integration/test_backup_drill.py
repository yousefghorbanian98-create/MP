"""تست مانور بکاپ/بازیابی (M30) — بکاپ ← حذف ← بازیابی ← تأیید یکپارچگی.

M97: `restore` دیگر فایل‌های الحاقی (registry.json / design-tokens.json) را در
مسیرهای زندهٔ source بازنویسی نمی‌کند؛ مانور باید روی scratch بماند، وگرنه خودِ
اجرای تست درخت کاری را تغییر می‌دهد.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from scripts.backup import EXTRA_FILES, backup, restore


def test_backup_drill_roundtrip(tmp_path: Path):
    db = tmp_path / "mp.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE members (id INTEGER PRIMARY KEY, name TEXT)")
    con.execute("INSERT INTO members VALUES (1, 'ورزشکار نمونه')")
    con.commit()
    con.close()

    live_before = {p: (p.read_bytes() if p.exists() else None) for p in EXTRA_FILES}

    archive = backup(tmp_path / "out", db_path=db)
    assert archive.exists()

    # «فاجعه»: حذف کامل دیتابیس
    db.unlink()

    manifest = restore(archive, db_path=db, extras_dir=tmp_path / "extras")
    assert manifest["files"].get("mp.db")

    con = sqlite3.connect(db)
    row = con.execute("SELECT name FROM members WHERE id=1").fetchone()
    con.close()
    assert row == ("ورزشکار نمونه",)  # داده بدون تغییر برگشت

    # مسیرهای واقعیِ source باید دست‌نخورده بمانند؛ فقط scratch نوشته شد
    for path, before in live_before.items():
        if before is not None:
            assert path.read_bytes() == before, f"مانور scratch نباید فایل زنده را عوض کند: {path}"


def test_backup_manifest_has_sha256(tmp_path: Path):
    import json
    import tarfile

    db = tmp_path / "mp.db"
    with sqlite3.connect(db) as con:
        con.execute("CREATE TABLE members (id INTEGER PRIMARY KEY)")
    archive = backup(tmp_path / "out", db_path=db)
    with tarfile.open(archive) as tar:
        m = json.load(tar.extractfile("manifest.json"))
    assert "mp.db" in m["files"]
    assert len(m["files"]["mp.db"]) == 64  # SHA256

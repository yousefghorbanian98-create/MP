"""بکاپ/بازیابی پایگاه‌داده و فایل‌های حیاتی — M23-c2 (E10).

استفاده:
    python scripts/backup.py backup  [--out DIR]      → فایل backup_YYYYmmdd_HHMMSS.tar.gz
    python scripts/backup.py restore ARCHIVE.tar.gz [--db PATH]

پشتیبان: دیتابیس (sqlite)، registry.json، design-tokens — با SHA256 داخل manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BACKEND_DIR / "mp.db"
EXTRA_FILES = [BACKEND_DIR / "modules" / "updates" / "registry.json"]


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def backup(out_dir: Path, db_path: Path = DEFAULT_DB) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    archive = out_dir / f"mp_backup_{stamp}.tar.gz"
    manifest = {"created_at": stamp, "files": {}}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        if db_path.exists():
            shutil.copy2(db_path, tmp_path / "mp.db")
            manifest["files"]["mp.db"] = _sha256(tmp_path / "mp.db")
        for f in EXTRA_FILES:
            if f.exists():
                shutil.copy2(f, tmp_path / f.name)
                manifest["files"][f.name] = _sha256(tmp_path / f.name)
        (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        with tarfile.open(archive, "w:gz") as tar:
            for item in tmp_path.iterdir():
                tar.add(item, arcname=item.name)
    return archive


def restore(archive: Path, db_path: Path = DEFAULT_DB) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(archive, "r:gz") as tar:
            tar.extractall(tmp)  # noqa: S202 — بکاپ خودی
        tmp_path = Path(tmp)
        manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        for name, expected in manifest["files"].items():
            src = tmp_path / name
            if _sha256(src) != expected:
                raise ValueError(f"hash mismatch for {name} — بکاپ خراب است")
        if "mp.db" in manifest["files"]:
            shutil.copy2(tmp_path / "mp.db", db_path)
        for f in EXTRA_FILES:
            src = tmp_path / f.name
            if src.exists():
                shutil.copy2(src, f)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="بکاپ/بازیابی MuscleParadise")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backup")
    b.add_argument("--out", type=Path, default=BACKEND_DIR / "backups")
    b.add_argument("--db", type=Path, default=DEFAULT_DB)
    r = sub.add_parser("restore")
    r.add_argument("archive", type=Path)
    r.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args(argv)
    if args.cmd == "backup":
        path = backup(args.out, args.db)
        print(f"backup created: {path}")
    else:
        manifest = restore(args.archive, args.db)
        print(f"restored {list(manifest['files'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

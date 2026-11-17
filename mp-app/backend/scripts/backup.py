"""بکاپ/بازیابی پایگاه‌داده و فایل‌های حیاتی — M23-c2 (E10).

استفاده:
    python scripts/backup.py backup  [--out DIR]      → فایل backup_YYYYmmdd_HHMMSS.tar.gz
    python scripts/backup.py restore ARCHIVE.tar.gz [--db PATH]

پشتیبان: دیتابیس SQLite، registry.json، design-tokens — با SHA256 داخل manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = BACKEND_DIR / "mp.db"
_SHARED_TOKENS = BACKEND_DIR.parent / "shared" / "design-tokens.json"
if not _SHARED_TOKENS.exists():
    # The `infra` image has the backend source at its workdir and copies shared
    # design tokens alongside it; local source uses the sibling `shared/` dir.
    _SHARED_TOKENS = BACKEND_DIR / "shared" / "design-tokens.json"
EXTRA_FILES = [
    BACKEND_DIR / "modules" / "updates" / "registry.json",
    _SHARED_TOKENS,
]
_ARCHIVE_FILES = {"manifest.json", "mp.db", *(path.name for path in EXTRA_FILES)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _snapshot_sqlite(source_path: Path, snapshot_path: Path) -> None:
    """Take a consistent SQLite snapshot (including WAL) and reject empty/corrupt DBs."""
    if not source_path.is_file():
        raise FileNotFoundError(
            f"database not found; refusing to create an empty backup: {source_path}"
        )
    source = None
    snapshot = None
    try:
        source_uri = f"{source_path.resolve().as_uri()}?mode=ro"
        source = sqlite3.connect(source_uri, uri=True)
        snapshot = sqlite3.connect(snapshot_path)
        source.backup(snapshot)
        integrity = snapshot.execute("PRAGMA integrity_check").fetchone()
        if integrity is None or integrity[0] != "ok":
            detail = integrity[0] if integrity else "no result"
            raise ValueError(f"database failed SQLite integrity_check: {detail}")
        tables = snapshot.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
              AND name <> 'alembic_version'
            """
        ).fetchall()
        if not tables:
            raise ValueError("empty database; refusing to create an empty backup")
    except sqlite3.Error as exc:
        raise ValueError(f"database is not a readable SQLite database: {source_path}") from exc
    finally:
        if snapshot is not None:
            snapshot.close()
        if source is not None:
            source.close()


def backup(out_dir: Path, db_path: Path = DEFAULT_DB) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    archive = out_dir / f"mp_backup_{stamp}.tar.gz"
    manifest = {"created_at": stamp, "files": {}}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _snapshot_sqlite(db_path, tmp_path / "mp.db")
        manifest["files"]["mp.db"] = _sha256(tmp_path / "mp.db")
        for path in EXTRA_FILES:
            if path.is_file():
                shutil.copy2(path, tmp_path / path.name)
                manifest["files"][path.name] = _sha256(tmp_path / path.name)
        (tmp_path / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        with tarfile.open(archive, "w:gz") as tar:
            for item in tmp_path.iterdir():
                tar.add(item, arcname=item.name)
    return archive


def _extract_archive(archive: Path, destination: Path) -> set[str]:
    """Extract only known regular files; never follow archive paths or links."""
    extracted: set[str] = set()
    with tarfile.open(archive, "r:gz") as tar:
        for member in tar.getmembers():
            name = PurePosixPath(member.name)
            if (
                member.name != name.as_posix()
                or len(name.parts) != 1
                or name.name not in _ARCHIVE_FILES
                or not member.isfile()
                or name.name in extracted
            ):
                raise ValueError(f"unsafe or unsupported backup member: {member.name}")
            source = tar.extractfile(member)
            if source is None:
                raise ValueError(f"backup member has no file data: {member.name}")
            target = destination / name.name
            with source, target.open("xb") as output:
                shutil.copyfileobj(source, output)
            extracted.add(name.name)
    return extracted


def _atomic_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=f".{destination.name}.",
            suffix=".restore-tmp",
            dir=destination.parent,
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
        shutil.copy2(source, temporary_path)
        os.replace(temporary_path, destination)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def restore(archive: Path, db_path: Path = DEFAULT_DB) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        extracted = _extract_archive(archive, tmp_path)
        if "manifest.json" not in extracted:
            raise ValueError("backup manifest is missing")
        try:
            manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("backup manifest is invalid") from exc

        files = manifest.get("files") if isinstance(manifest, dict) else None
        if not isinstance(files, dict) or "mp.db" not in files:
            raise ValueError("backup manifest must include mp.db")
        archived_files = extracted - {"manifest.json"}
        if archived_files != set(files):
            raise ValueError("backup archive members do not match the manifest")

        for name, expected_hash in files.items():
            if (
                name not in _ARCHIVE_FILES - {"manifest.json"}
                or not isinstance(expected_hash, str)
                or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
            ):
                raise ValueError(f"invalid backup manifest entry: {name!r}")
            source = tmp_path / name
            if _sha256(source) != expected_hash:
                raise ValueError(f"hash mismatch for {name} — backup is corrupt")

        # Re-validate the restored database before replacing the operator's file.
        validated_db = tmp_path / "validated.db"
        _snapshot_sqlite(tmp_path / "mp.db", validated_db)
        _atomic_copy(validated_db, db_path)

        for path in EXTRA_FILES:
            archived_path = tmp_path / path.name
            if path.name in files:
                _atomic_copy(archived_path, path)
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="بکاپ/بازیابی MuscleParadise")
    sub = parser.add_subparsers(dest="cmd", required=True)
    backup_parser = sub.add_parser("backup")
    backup_parser.add_argument("--out", type=Path, default=BACKEND_DIR / "backups")
    backup_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    restore_parser = sub.add_parser("restore")
    restore_parser.add_argument("archive", type=Path)
    restore_parser.add_argument("--db", type=Path, default=DEFAULT_DB)
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

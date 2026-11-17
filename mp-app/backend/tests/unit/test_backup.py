from __future__ import annotations

import hashlib
import io
import json
import sqlite3
import tarfile
from pathlib import Path

import pytest

from scripts.backup import backup, restore


def _create_database(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE members (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        conn.execute("INSERT INTO members(name) VALUES ('test member')")


def test_backup_fails_closed_for_missing_or_empty_database(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        backup(tmp_path / "backups", tmp_path / "missing.db")

    empty = tmp_path / "empty.db"
    sqlite3.connect(empty).close()
    with pytest.raises(ValueError, match="empty database"):
        backup(tmp_path / "backups", empty)


def test_backup_and_restore_existing_database(tmp_path: Path) -> None:
    source = tmp_path / "source.db"
    _create_database(source)
    archive = backup(tmp_path / "archives", source)
    target = tmp_path / "restored.db"
    manifest = restore(archive, target)

    assert "mp.db" in manifest["files"]
    with sqlite3.connect(target) as conn:
        assert conn.execute("SELECT name FROM members").fetchone() == ("test member",)


def test_backup_rejects_non_sqlite_or_corrupt_database(tmp_path: Path) -> None:
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"not sqlite")
    with pytest.raises(ValueError, match="readable SQLite"):
        backup(tmp_path / "archives", corrupt)


@pytest.mark.parametrize(
    ("member_name", "member_type", "linkname"),
    [
        ("../escaped.db", tarfile.REGTYPE, ""),
        ("mp.db", tarfile.SYMTYPE, "../../etc/passwd"),
    ],
)
def test_restore_rejects_traversal_and_link_members(
    tmp_path: Path, member_name: str, member_type: bytes, linkname: str
) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        member = tarfile.TarInfo(member_name)
        member.type = member_type
        member.linkname = linkname
        if member.isfile():
            content = b"unsafe"
            member.size = len(content)
            tar.addfile(member, io.BytesIO(content))
        else:
            tar.addfile(member)

    with pytest.raises(ValueError, match="unsafe or unsupported"):
        restore(archive, tmp_path / "restored.db")


def test_backup_manifest_hash_matches_consistent_snapshot(tmp_path: Path) -> None:
    db = tmp_path / "mp.db"
    _create_database(db)
    archive = backup(tmp_path / "archives", db)
    with tarfile.open(archive) as tar:
        manifest = json.load(tar.extractfile("manifest.json"))
        database_snapshot = tar.extractfile("mp.db").read()

    assert manifest["files"]["mp.db"] == hashlib.sha256(database_snapshot).hexdigest()

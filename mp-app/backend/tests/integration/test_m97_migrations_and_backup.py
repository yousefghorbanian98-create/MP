"""M97 — مهاجرت‌ها: تاریخچهٔ یک‌سر، drift جدا از schema مدل‌ساخته، و مانور backup/restore.

سه پرسش که پیش از این هیچ‌کدام تنها پاسخ نمی‌داد:

1. **آیا دو مسیر provisioning همان schema را می‌سازند؟** تست M47 با `alembic check`
   می‌سنجد «DB مهاجرت‌کرده = مدل». اما dev/test با `Base.metadata.create_all`
   (`db/base.py: init_db`) می‌سازند؛ اگر migrations مسیری رفته باشند که create_all
   نمی‌سازد (یا برعکس)، `alembic check` آن را نمی‌بیند. این‌جا همان schema از دو
   مسیر ساخته و جدول‌به‌جدول مقایسه می‌شود.
2. **تاریخچهٔ migration سالم است؟** یک head، بدون revision تکراری، بدون
   `down_revision` گم‌شده و بدون یتیم. دو head یعنی `alembic upgrade head` در
   استقرار بعدی می‌شکند؛ تاریخچهٔ همین پروژه یک بار merge head خورده است، پس این
   گیت باید بماند.
3. **restore واقعاً تمرین‌پذیر است؟** `restore` فایل‌های الحاقی را همیشه در
   مسیرهای زنده می‌نوشت؛ مانور ماهانهٔ «restore به مسیر موقت» که OPS-RUNBOOK
   لازم می‌داند عملاً ممکن نبود. حالا `verify` (بدون نوشتن) و
   `restore --extras-to` سنجیده می‌شوند.

هیچ دیتابیس واقعی/تولیدی لمس نمی‌شود: همه‌چیز SQLite موقت زیر `tmp_path` است.
"""

from __future__ import annotations

import io
import os
import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
VERSIONS = BACKEND / "db" / "migrations" / "versions"


def _alembic(db_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "MP_DATABASE_URL": f"sqlite:///{db_path}"}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
        timeout=240,
    )


@pytest.fixture(scope="module")
def migrated_db(tmp_path_factory) -> Path:
    """یک DB scratch که فقط خوانده می‌شود؛ چند تست از همان یک‌بار ساخت استفاده می‌کنند."""
    db = tmp_path_factory.mktemp("m97") / "migrated.db"
    result = _alembic(db, "upgrade", "head")
    assert result.returncode == 0, f"upgrade head شکست خورد:\n{result.stderr[-2000:]}"
    return db


def _schema(db_path: Path) -> dict[str, tuple[dict[str, tuple[str, bool]], set[str]]]:
    """نقشهٔ schema: جدول ← ({ستون: (نوع، nullable)}, {نام ایندکس‌های دستی}).

    ایندکس‌های `sqlite_autoindex_*` حذف می‌شوند: SQLite آن‌ها را از UNIQUE/PK خودش
    می‌سازد و نامشان بین دو مسیر provisioning تضمینی نیست.
    """
    con = sqlite3.connect(db_path)
    try:
        out: dict[str, tuple[dict[str, tuple[str, bool]], set[str]]] = {}
        tables = [
            row[0]
            for row in con.execute(
                "select name from sqlite_master where type='table' "
                "and name not like 'sqlite_%' and name <> 'alembic_version' order by name"
            )
        ]
        for table in tables:
            columns = {
                row[1]: (str(row[2]).upper(), bool(row[3]))
                for row in con.execute("select * from pragma_table_info(?)", (table,))
            }
            indexes = {
                row[1]
                for row in con.execute("select * from pragma_index_list(?)", (table,))
                if not str(row[1]).startswith("sqlite_autoindex")
            }
            out[table] = (columns, indexes)
        return out
    finally:
        con.close()


def test_create_all_and_migrations_build_the_same_schema(tmp_path, migrated_db) -> None:
    """driftِ مسیر مدل (create_all) از driftِ مسیر migration جدا سنجیده می‌شود.

    اگر این تست بشکند، باید تصمیم گرفته شود کدام مسیر مرجع است و یک migration
    اصلاحی اضافه شود — نه اینکه create_all یا migration یک‌طرفه «درست» اعلام شوند.
    """
    from sqlalchemy import create_engine

    import db.models  # noqa: F401  — ثبت جدول‌ها روی metadata
    from db.base import Base

    scratch = tmp_path / "created_all.db"
    engine = create_engine(f"sqlite:///{scratch}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    migrated = _schema(migrated_db)
    created = _schema(scratch)

    assert set(migrated) == set(created), (
        "جدول‌ها فرق دارند — "
        f"فقط در migrations: {sorted(set(migrated) - set(created))}، "
        f"فقط در create_all: {sorted(set(created) - set(migrated))}"
    )
    assert migrated, "هر دو schema خالی‌اند؛ fixture یا مدل‌ها بارگذاری نشده‌اند"

    for table in sorted(migrated):
        mig_cols, mig_idx = migrated[table]
        crt_cols, crt_idx = created[table]
        assert mig_cols == crt_cols, f"ستون‌های {table} یکسان نیستند"
        assert mig_idx == crt_idx, (
            f"ایندکس‌های {table} یکسان نیستند — "
            f"فقط migrations: {sorted(mig_idx - crt_idx)}، "
            f"فقط create_all: {sorted(crt_idx - mig_idx)}"
        )


def test_existing_create_all_database_can_be_baselined_by_migrations(tmp_path, migrated_db) -> None:
    """نصب قدیمی که با create_all ساخته شده، پس از `stamp head` بی‌drift بالا می‌آید.

    این همان «baseline» است که معیار پذیرش M97 می‌خواهد: اصلاح schema فقط با
    baseline + migration آزموده، نه با دست‌کاری DB.
    """
    from sqlalchemy import create_engine

    import db.models  # noqa: F401
    from db.base import Base

    legacy = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{legacy}")
    Base.metadata.create_all(bind=engine)
    engine.dispose()

    assert _schema(legacy) == _schema(migrated_db)

    stamp = _alembic(legacy, "stamp", "head")
    assert stamp.returncode == 0, f"stamp head شکست خورد:\n{stamp.stderr[-2000:]}"

    current = _alembic(legacy, "current")
    assert current.returncode == 0
    assert "head" in (current.stdout + current.stderr), current.stdout[-1000:]

    check = _alembic(legacy, "check")
    assert "No new upgrade operations detected" in (check.stdout + check.stderr), (
        "DB مهاجرت‌نکرده پس از baseline هنوز drift دارد:\n" + (check.stdout + check.stderr)[-2000:]
    )


def test_migration_history_has_one_head_and_no_broken_links() -> None:
    """تاریخچهٔ migration: یک head، بدون حلقهٔ گم‌شده، بدون یتیم، بدون فایل بیرون گراف."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    script = ScriptDirectory.from_config(Config(str(BACKEND / "alembic.ini")))
    revisions = list(script.walk_revisions())
    ids = [rev.revision for rev in revisions]

    assert len(ids) == len(set(ids)), (
        f"revision تکراری: {sorted({i for i in ids if ids.count(i) > 1})}"
    )

    heads = script.get_heads()
    assert len(heads) == 1, f"بیش از یک head وجود دارد ({heads}) — `upgrade head` می‌شکند"

    known = set(ids)
    parents = {
        parent
        for rev in revisions
        for parent in (
            [rev.down_revision]
            if isinstance(rev.down_revision, str)
            else list(rev.down_revision or [])
        )
    }
    missing = sorted(parents - known)
    assert not missing, f"down_revision به revision ناموجود اشاره می‌کند: {missing}"

    # هر revision باید از head قابل رسیدن به عقب باشد؛ یتیم یعنی از دست رفتن migration
    unreachable = sorted((known - parents) - set(heads))
    assert not unreachable, f"revision بدون فرزند (یتیم، head نیست): {unreachable}"

    files = sorted(p.name for p in VERSIONS.glob("*.py"))
    loaded = sorted(Path(rev.module.__file__).name for rev in revisions)
    assert files == loaded, (
        "فایل migration در گراف نیست (یا برعکس) — "
        f"فقط فایل: {sorted(set(files) - set(loaded))}، فقط گراف: {sorted(set(loaded) - set(files))}"
    )


def test_backup_verify_and_scratch_restore(tmp_path, migrated_db) -> None:
    """مانور کامل: backup ← verify ← restore به scratch، بدون لمس فایل‌های زنده.

    `verify` باید بدون نوشتن، hash/manifest/integrity را تأیید کند و نسخهٔ
    alembic داخل آرشیو را گزارش دهد. `restore --extras-to` باید DB و فایل‌های
    الحاقی را فقط در مسیر موقت بنویسد — مسیرهای واقعی بایت‌به‌بایت عوض نشوند.
    """
    from scripts.backup import EXTRA_FILES, backup, restore, verify

    live_before = {p: (p.read_bytes() if p.exists() else None) for p in EXTRA_FILES}

    archive = backup(tmp_path / "out", db_path=migrated_db)
    assert archive.exists() and archive.name.startswith("mp_backup_")

    summary = verify(archive)
    assert summary["tables"] == len(_schema(migrated_db))
    assert summary["alembic_revision"] == script_head(), (
        "آرشیو باید نسخهٔ مهاجرت head را حمل کند، وگرنه restore به schema قدیمی می‌برد"
    )
    assert summary["files"]["mp.db"] and len(summary["files"]["mp.db"]) == 64

    restored = tmp_path / "restored.db"
    extras = tmp_path / "extras"
    manifest = restore(archive, db_path=restored, extras_dir=extras)
    assert manifest["files"]["mp.db"] == summary["files"]["mp.db"]

    assert _schema(restored) == _schema(migrated_db), "schema پس از restore عوض شده است"
    # DB بازگردانده‌شده باید همان مسیر استقرار را ادامه دهد: بدون drift و روی head
    check = _alembic(restored, "check")
    assert "No new upgrade operations detected" in (check.stdout + check.stderr)

    for path in EXTRA_FILES:
        if path.name in manifest["files"]:
            assert (extras / path.name).is_file(), f"فایل الحاقی به scratch نرفت: {path.name}"
            assert (extras / path.name).read_bytes() == path.read_bytes()
        assert (live_before[path] is None) == (not path.exists())
        if live_before[path] is not None:
            assert path.read_bytes() == live_before[path], (
                f"restore به scratch نباید فایل زنده را بازنویسی کند: {path}"
            )


def test_verify_rejects_a_tampered_archive(tmp_path, migrated_db) -> None:
    """آرشیوی که فقط یک بایتش فرق کند، پیش از هر نوشتن رد می‌شود (نه بعد از restore)."""
    from scripts.backup import backup, verify

    archive = backup(tmp_path / "out", db_path=migrated_db)
    tampered = tmp_path / "tampered.tar.gz"
    with tarfile.open(archive, "r:gz") as src, tarfile.open(tampered, "w:gz") as dst:
        for member in src.getmembers():
            handle = src.extractfile(member)
            assert handle is not None
            data = handle.read()
            if member.name == "mp.db":
                data += b"\x00"  # دست‌کاری بیرونی، بدون به‌روزرسانی manifest
            info = tarfile.TarInfo(member.name)
            info.size = len(data)
            dst.addfile(info, io.BytesIO(data))

    with pytest.raises(ValueError, match="hash mismatch"):
        verify(tampered)


def script_head() -> str:
    """head فعلی تاریخچه — از خود Alembic، نه از یک عدد در تست."""
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    heads = ScriptDirectory.from_config(Config(str(BACKEND / "alembic.ini"))).get_heads()
    assert len(heads) == 1, f"چند head: {heads}"
    return heads[0]

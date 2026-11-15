"""ورود کاتالوگ حرکات free-exercise-db (M33-c1).

کاربرد:
    python scripts/import_exercise_catalog.py            # ورود/به‌روزرسانی از فایل vendor
    python scripts/import_exercise_catalog.py --check    # فقط راستی‌آزمایی sha256

E12: منبع + مجوز + digest پیش از ادغام ثبت می‌شود. دادهٔ واقعی کاربران هرگز در این مسیر نیست.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.base import get_session_factory  # noqa: E402
from db.models.content import CatalogExercise, CatalogSource  # noqa: E402

SOURCE_NAME = "free-exercise-db"
SOURCE_URL = "https://github.com/yuhonas/free-exercise-db"
SOURCE_COMMIT = "f00c92c7dcf1216a928a52c3706c7ce8e2f71ed5"
SOURCE_LICENSE = "Unlicense"
DEFAULT_DATA = (
    Path(__file__).resolve().parents[1] / "data" / "external" / "free_exercise_db" / "exercises.json"
)
EXPECTED_DIGEST = "5bb747e3fc658f095a60dcbf6d53c96627acdcc6ffb6fffde86f7e26995d40bf"


@dataclass
class ImportResult:
    source_id: int
    inserted: int
    updated: int

    @property
    def total(self) -> int:
        return self.inserted + self.updated


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(path: Path) -> str:
    """راستی‌آزمایی یکپارچگی فایل منبع — digest باید با ثبت منبع بخواند."""
    digest = file_digest(path)
    if digest != EXPECTED_DIGEST:
        raise ValueError(f"digest mismatch for {path.name}: {digest} != {EXPECTED_DIGEST}")
    return digest


def import_catalog(session: Session, path: Path = DEFAULT_DATA) -> ImportResult:
    """کاتالوگ را در دیتابیس upsert می‌کند (idempotent — قابل اجرای مجدد)."""
    digest = verify_source(path)
    rows = json.loads(path.read_text(encoding="utf-8"))

    source = session.query(CatalogSource).filter_by(name=SOURCE_NAME).one_or_none()
    if source is None:
        source = CatalogSource(
            name=SOURCE_NAME,
            upstream_url=SOURCE_URL,
            upstream_commit=SOURCE_COMMIT,
            license=SOURCE_LICENSE,
            digest=digest,
            exercise_count=len(rows),
        )
        session.add(source)
        session.flush()
    else:
        source.upstream_commit = SOURCE_COMMIT
        source.digest = digest
        source.exercise_count = len(rows)

    inserted = 0
    updated = 0
    for row in rows:
        external_id = str(row.get("id", "")).strip()
        if not external_id:
            raise ValueError("catalog row without id")
        payload = {
            "source_id": source.id,
            "name": str(row.get("name", "")).strip(),
            "category": str(row.get("category", "")),
            "level": str(row.get("level", "")),
            "force": str(row.get("force", "")),
            "mechanic": str(row.get("mechanic", "")),
            "equipment": str(row.get("equipment", "")),
            "primary_muscles": json.dumps(row.get("primaryMuscles", []), ensure_ascii=False),
            "secondary_muscles": json.dumps(row.get("secondaryMuscles", []), ensure_ascii=False),
            "instructions": json.dumps(row.get("instructions", []), ensure_ascii=False),
            "image_refs": json.dumps(row.get("images", []), ensure_ascii=False),
        }
        existing = session.query(CatalogExercise).filter_by(external_id=external_id).one_or_none()
        if existing is None:
            session.add(CatalogExercise(external_id=external_id, **payload))
            inserted += 1
        else:
            for key, value in payload.items():
                setattr(existing, key, value)
            updated += 1

    session.commit()
    return ImportResult(source_id=source.id, inserted=inserted, updated=updated)


def main() -> int:
    parser = argparse.ArgumentParser(description="import free-exercise-db catalog")
    parser.add_argument("--check", action="store_true", help="only verify source digest")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    args = parser.parse_args()

    if args.check:
        digest = verify_source(args.data)
        print(f"OK digest {digest}")
        return 0

    session = get_session_factory()()
    try:
        result = import_catalog(session, args.data)
        print(
            f"catalog imported: source_id={result.source_id} "
            f"inserted={result.inserted} updated={result.updated} total={result.total}"
        )
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

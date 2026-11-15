"""m58_c1 — حذف دو index یتیم روی updated_at

Revision ID: 8a1f2c3d4e5b
Revises: 67f8b00508eb

چرا: migration اولیه `ix_class_bookings_updated_at` و
`ix_gym_classes_updated_at` را می‌ساخت، ولی هیچ مدلی این indexها را
تعریف نمی‌کند. نتیجه: `alembic check` همیشه drift نشان می‌داد و
`test_m47_migration_drift` فقط با drop_indexهای دستی داخل یک migration
دیگر سبز می‌شد (بوی بد). حالا صریح و مستند حذف می‌شوند.

هزینه: حذف index روی updated_at برای این دو جدول کوچک بی‌اثر است؛
هیچ کوئری‌ای بر اساس updated_at فیلتر نمی‌کند (grep شد).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "8a1f2c3d4e5b"
down_revision: str | Sequence[str] | None = "67f8b00508eb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_INDEXES = (
    ("ix_class_bookings_updated_at", "class_bookings"),
    ("ix_gym_classes_updated_at", "gym_classes"),
)


def _existing(table: str) -> set[str]:
    from sqlalchemy import inspect

    insp = inspect(op.get_bind())
    if table not in insp.get_table_names():
        return set()
    return {ix["name"] for ix in insp.get_indexes(table)}


def upgrade() -> None:
    # idempotent: DBهایی که با create_all ساخته شده‌اند این indexها را
    # ندارند (مدل تعریفشان نمی‌کند)؛ باید بی‌خطا رد شوند.
    for name, table in _INDEXES:
        if name in _existing(table):
            op.drop_index(name, table_name=table)


def downgrade() -> None:
    for name, table in _INDEXES:
        if name not in _existing(table):
            op.create_index(name, table, ["updated_at"])

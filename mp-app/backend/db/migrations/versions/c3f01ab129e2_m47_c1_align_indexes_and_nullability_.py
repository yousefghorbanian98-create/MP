"""M47-c1 — هم‌ترازی schema با مدل‌ها (ایندکس‌های گم‌شده + nullable)

این drift پیش از M45 وجود داشت و در بازبینی REA ثبت شد:
مدل‌ها `TimestampMixin` و `BranchMixin` دارند که `index=True` و
`nullable=False` می‌خواهند، ولی migrationهای اولیه این‌ها را نداشتند.

چرا «دستی» نوشته شده و نه خام autogenerate:
  ۱) SQLite برای تغییر nullable به batch mode نیاز دارد (بازسازی جدول)؛
     alter_column مستقیم در SQLite بی‌اثر است و بی‌صدا رد می‌شود.
  ۲) اگر ردیفی با NULL وجود داشته باشد، NOT NULL کردن بی‌مقدمه شکست می‌خورد.
     پس ابتدا backfill می‌کنیم، بعد NOT NULL می‌گذاریم.

Revision ID: c3f01ab129e2
Revises: f1a2b3c4d5e6
Create Date: 2026-11-15
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3f01ab129e2"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (جدول, ستون‌های زمانی, ستون branch_id)
_TIMESTAMP_TABLES = [
    ("axis_assessments", ("created_at",), False),
    ("catalog_exercises", ("created_at",), False),
    ("catalog_sources", ("created_at",), False),
    ("class_bookings", ("created_at", "updated_at"), True),
    ("gym_classes", ("created_at", "updated_at"), True),
    ("norm_entries", ("created_at",), False),
    ("progression_ladders", ("created_at",), False),
    ("progression_steps", ("created_at",), False),
    ("set_feedbacks", ("created_at",), False),
]


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    # ── ۱) ایندکس‌ها (برای همهٔ دیالکت‌ها) ──
    for table, ts_cols, has_branch in _TIMESTAMP_TABLES:
        for col in ts_cols:
            idx = f"ix_{table}_{col}"
            op.create_index(op.f(idx), table, [col], unique=False)
        if has_branch:
            op.create_index(op.f(f"ix_{table}_branch_id"), table, ["branch_id"], unique=False)

    # ایندکس‌های کلید خارجی که مدل‌ها با index=True دارند
    op.create_index(
        op.f("ix_class_bookings_class_id"), "class_bookings", ["class_id"], unique=False
    )
    op.create_index(
        op.f("ix_class_bookings_member_id"), "class_bookings", ["member_id"], unique=False
    )

    # ── ۲) ایندکس‌های اضافی ──
    # migration اولیه ix_<table>_updated_at را ساخت، ولی TimestampMixin فقط
    # created_at را ایندکس می‌کند. batch_alter_table در SQLite آن‌ها را حفظ
    # می‌کند، پس صریح حذف می‌شوند تا schema = مدل شود.
    for table in ("class_bookings", "gym_classes"):
        op.execute(f"DROP INDEX IF EXISTS ix_{table}_updated_at")  # noqa: S608

    # ── ۳) nullable → NOT NULL، با backfill قبلی ──
    nullable_fixes = [
        ("class_bookings", "created_at"),
        ("class_bookings", "updated_at"),
        ("gym_classes", "created_at"),
        ("gym_classes", "updated_at"),
    ]

    for table, col in nullable_fixes:
        # backfill: ردیف‌های NULL باید مقدار بگیرند، وگرنه NOT NULL شکست می‌خورد
        bind.execute(
            sa.text(
                f"UPDATE {table} SET {col} = CURRENT_TIMESTAMP WHERE {col} IS NULL"  # noqa: S608
            )
        )

    if is_sqlite:
        # SQLite: بازسازی جدول لازم است (batch)
        with op.batch_alter_table("class_bookings") as batch:
            batch.alter_column(
                "created_at",
                existing_type=sa.DATETIME(),
                nullable=False,
                existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            )
            batch.alter_column(
                "updated_at",
                existing_type=sa.DATETIME(),
                nullable=False,
                existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            )
        with op.batch_alter_table("gym_classes") as batch:
            batch.alter_column(
                "created_at",
                existing_type=sa.DATETIME(),
                nullable=False,
                existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            )
            batch.alter_column(
                "updated_at",
                existing_type=sa.DATETIME(),
                nullable=False,
                existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            )
    else:
        for table, col in nullable_fixes:
            op.alter_column(
                table,
                col,
                existing_type=sa.DATETIME(),
                nullable=False,
                existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            )


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == "sqlite"

    nullable_reverts = [
        ("class_bookings", "created_at"),
        ("class_bookings", "updated_at"),
        ("gym_classes", "created_at"),
        ("gym_classes", "updated_at"),
    ]

    if is_sqlite:
        # SQLite: ALTER COLUMN پشتیبانی نمی‌شود، batch لازم است
        for table in ("class_bookings", "gym_classes"):
            with op.batch_alter_table(table) as batch:
                for col in ("created_at", "updated_at"):
                    batch.alter_column(
                        col,
                        existing_type=sa.DATETIME(),
                        nullable=True,
                        existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    )
    else:
        for table, col in nullable_reverts:
            op.alter_column(
                table,
                col,
                existing_type=sa.DATETIME(),
                nullable=True,
                existing_server_default=sa.text("(CURRENT_TIMESTAMP)"),
            )

    # batch_alter_table هنگام بازسازی، ایندکس‌های جدول را هم بازمی‌سازد؛
    # پس حذف باید IF EXISTS باشد، وگرنه downgrade می‌شکند.
    for idx in (
        "ix_class_bookings_member_id",
        "ix_class_bookings_class_id",
    ):
        op.execute(f"DROP INDEX IF EXISTS {idx}")  # noqa: S608

    for table, ts_cols, has_branch in _TIMESTAMP_TABLES:
        for col in ts_cols:
            op.execute(f"DROP INDEX IF EXISTS ix_{table}_{col}")  # noqa: S608
        if has_branch:
            op.execute(f"DROP INDEX IF EXISTS ix_{table}_branch_id")  # noqa: S608

"""M35-c1 — جدول نُرم‌های صدکی/معیاری آزمون‌های میدانی (norm_entries)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a7b8c9d0e1f2"
down_revision = "f6a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "norm_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("test_key", sa.String(length=40), nullable=False, index=True),
        sa.Column("name_fa", sa.String(length=120), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False, server_default="percentile"),
        sa.Column("sex", sa.String(length=10), nullable=False),
        sa.Column("age_min", sa.Integer(), nullable=False),
        sa.Column("age_max", sa.Integer(), nullable=False),
        sa.Column("percentiles", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("bands", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("sdc", sa.Float(), nullable=True),
        sa.Column("sdc_note", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("source", sa.String(length=300), nullable=False),
        sa.Column("source_version", sa.String(length=60), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("test_key", "sex", "age_min", "age_max", name="uq_norm_test_sex_age"),
    )


def downgrade() -> None:
    op.drop_table("norm_entries")

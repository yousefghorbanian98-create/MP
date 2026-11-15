"""M34-c1 — نردبان‌های پیشرفت (progression_ladders + progression_steps)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f6a1b2c3d4e5"
down_revision = "e5f6a1b2c3d4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "progression_ladders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(length=60), nullable=False, unique=True),
        sa.Column("name_fa", sa.String(length=120), nullable=False),
        sa.Column("axis_focus", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "progression_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ladder_key", sa.String(length=60), nullable=False, index=True),
        sa.Column("step_no", sa.Integer(), nullable=False),
        sa.Column("catalog_external_id", sa.String(length=60), nullable=False, index=True),
        sa.Column("name_fa", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("progression_steps")
    op.drop_table("progression_ladders")

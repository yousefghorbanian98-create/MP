"""M33-c1 — کاتالوگ حرکات (free-exercise-db) + ثبت منبع (E12)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c3d4e5f6a1b2"
down_revision = "b2c3d4e5f6a1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "catalog_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False, unique=True),
        sa.Column("upstream_url", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("upstream_commit", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("license", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("digest", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("exercise_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "catalog_exercises",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), nullable=False, index=True),
        sa.Column("external_id", sa.String(length=60), nullable=False, index=True),
        sa.Column("name", sa.String(length=160), nullable=False, index=True),
        sa.Column("category", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("level", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("force", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("mechanic", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("equipment", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("primary_muscles", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("secondary_muscles", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("instructions", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("image_refs", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("catalog_exercises")
    op.drop_table("catalog_sources")

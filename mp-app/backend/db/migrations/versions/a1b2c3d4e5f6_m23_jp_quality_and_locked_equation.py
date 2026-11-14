"""M23 — فیلدهای E02 (quality/method) + نسخهٔ معادله + nullable شدن body_fat_pct (E07/D-012).

Revision ID: a1b2c3d4e5f6
Revises: 39f0cd2d8531
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "39f0cd2d8531"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("jackson_pollock_measurements") as batch:
        batch.add_column(
            sa.Column(
                "equation_version",
                sa.String(length=64),
                nullable=False,
                server_default="LOCKED:pending-independent-reference",
            )
        )
        batch.add_column(sa.Column("quality", sa.String(length=32), nullable=True))
        batch.add_column(sa.Column("method", sa.String(length=64), nullable=True))
        batch.alter_column("body_fat_pct", existing_type=sa.Float(), nullable=True)


def downgrade() -> None:
    with op.batch_alter_table("jackson_pollock_measurements") as batch:
        batch.alter_column("body_fat_pct", existing_type=sa.Float(), nullable=False)
        batch.drop_column("method")
        batch.drop_column("quality")
        batch.drop_column("equation_version")

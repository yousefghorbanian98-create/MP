"""Worker heartbeats for dead-worker detection and queue gauges (QF-27).

Revision ID: d8e9f0a1b2c3
Revises: c7d8e9f0a1b2
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d8e9f0a1b2c3"
down_revision: str | Sequence[str] | None = "c7d8e9f0a1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "worker_heartbeats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("worker_key", sa.String(length=40), nullable=False, unique=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_result", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    op.drop_table("worker_heartbeats")

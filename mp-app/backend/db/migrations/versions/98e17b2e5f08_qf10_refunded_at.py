"""Payment refund timestamp for periodic finance report (phase 6, QF-10).

Revision ID: 98e17b2e5f08
Revises: d8e9f0a1b2c3
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "98e17b2e5f08"
down_revision: str | Sequence[str] | None = "d8e9f0a1b2c3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("payments") as batch:
        batch.add_column(sa.Column("refunded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch:
        batch.drop_column("refunded_at")

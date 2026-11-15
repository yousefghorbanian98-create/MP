"""M42-c2 — ثبت خروج از باشگاه (checkout) برای محاسبهٔ زمان حضور."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e0f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "checkins", sa.Column("checked_out_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("checkins", "checked_out_at")

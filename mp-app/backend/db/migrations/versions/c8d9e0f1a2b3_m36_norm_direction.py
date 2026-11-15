"""M36-c2 — فیلد direction روی norm_entries (کوپر: کمتر بهتر)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("norm_entries") as batch:
        batch.add_column(sa.Column("direction", sa.String(length=20), nullable=False, server_default="higher_better"))


def downgrade() -> None:
    with op.batch_alter_table("norm_entries") as batch:
        batch.drop_column("direction")

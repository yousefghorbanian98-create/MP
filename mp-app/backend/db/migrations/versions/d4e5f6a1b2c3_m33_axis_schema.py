"""M33-c2 — بردار پوشش ۱۴محوره + باند شدت + پیوند نردبان روی catalog_exercises."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a1b2c3"
down_revision = "c3d4e5f6a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("catalog_exercises") as batch:
        batch.add_column(sa.Column("axis_coverage", sa.Text(), nullable=False, server_default="{}"))
        batch.add_column(sa.Column("intensity_band", sa.String(length=20), nullable=False, server_default=""))
        batch.add_column(sa.Column("progression_key", sa.String(length=60), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("catalog_exercises") as batch:
        batch.drop_column("progression_key")
        batch.drop_column("intensity_band")
        batch.drop_column("axis_coverage")

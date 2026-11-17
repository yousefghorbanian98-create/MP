"""M33-c3 — مهاجرت: نام فارسی + وضعیت review روی catalog_exercises."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e5f6a1b2c3d4"
down_revision = "d4e5f6a1b2c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("catalog_exercises") as batch:
        batch.add_column(
            sa.Column("name_fa", sa.String(length=160), nullable=False, server_default="")
        )
        batch.add_column(
            sa.Column(
                "review_status", sa.String(length=16), nullable=False, server_default="candidate"
            )
        )
        batch.add_column(sa.Column("review_meta", sa.Text(), nullable=False, server_default="{}"))


def downgrade() -> None:
    with op.batch_alter_table("catalog_exercises") as batch:
        batch.drop_column("review_meta")
        batch.drop_column("review_status")
        batch.drop_column("name_fa")

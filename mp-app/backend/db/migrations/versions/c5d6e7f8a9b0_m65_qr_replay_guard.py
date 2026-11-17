"""M65 — persist QR jti digests and enforce one-time redemption.

Revision ID: c5d6e7f8a9b0
Revises: b7c9d1e2f3a4
Create Date: 2026-11-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "c5d6e7f8a9b0"
down_revision = "b7c9d1e2f3a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("checkins", sa.Column("qr_jti_hash", sa.String(length=64), nullable=True))
    op.create_index("uq_checkins_qr_jti_hash", "checkins", ["qr_jti_hash"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_checkins_qr_jti_hash", table_name="checkins")
    op.drop_column("checkins", "qr_jti_hash")

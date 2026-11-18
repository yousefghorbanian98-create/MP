"""Persist the gateway refund reference independently of the payment reference.

Revision ID: b19c28d37e46
Revises: f9b0c1d2e3f4
"""

import sqlalchemy as sa
from alembic import op

revision = "b19c28d37e46"
down_revision = "f9b0c1d2e3f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("payments", sa.Column("refund_reference", sa.String(length=80), nullable=True))


def downgrade() -> None:
    op.drop_column("payments", "refund_reference")

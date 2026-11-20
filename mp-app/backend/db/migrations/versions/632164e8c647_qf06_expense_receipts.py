"""Private optional receipt per expense (phase 6, QF-06).

Revision ID: 632164e8c647
Revises: 98e17b2e5f08
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "632164e8c647"
down_revision: str | Sequence[str] | None = "98e17b2e5f08"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "expense_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "expense_id",
            sa.Integer(),
            sa.ForeignKey("expenses.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("stored_path", sa.String(length=300), nullable=False),
        sa.Column("mime", sa.String(length=30), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "uploaded_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("expense_receipts")

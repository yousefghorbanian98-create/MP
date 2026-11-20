"""Append-only member money ledger with reversal (phase 6 loop 2, QF-05).

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a5b6c7d8e9f0"
down_revision: str | Sequence[str] | None = "f4a5b6c7d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "ledger_entries"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "member_id",
            sa.Integer(),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_rial", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("idempotency_key", sa.String(length=80), nullable=True),
        sa.Column(
            "reverses_entry_id",
            sa.Integer(),
            sa.ForeignKey(f"{_TABLE}.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reversed_by_entry_id",
            sa.Integer(),
            sa.ForeignKey(f"{_TABLE}.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.String(length=200), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_ledger_entries_member_id", _TABLE, ["member_id"])
    op.create_index(
        "uq_ledger_entries_idempotency",
        _TABLE,
        ["idempotency_key"],
        unique=True,
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_ledger_entries_idempotency", table_name=_TABLE)
    op.drop_index("ix_ledger_entries_member_id", table_name=_TABLE)
    op.drop_table(_TABLE)

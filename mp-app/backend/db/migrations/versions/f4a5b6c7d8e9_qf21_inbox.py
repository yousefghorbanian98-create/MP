"""Inbox messages: at-least-once delivery with a one-time effect (phase 8, QF-21).

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f4a5b6c7d8e9"
down_revision: str | Sequence[str] | None = "e3f4a5b6c7d8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLE = "inbox_messages"


def upgrade() -> None:
    op.create_table(
        _TABLE,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(length=60), nullable=False),
        sa.Column("dedup_key", sa.String(length=120), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("uq_inbox_messages_topic_key", _TABLE, ["topic", "dedup_key"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_inbox_messages_topic_key", table_name=_TABLE)
    op.drop_table(_TABLE)

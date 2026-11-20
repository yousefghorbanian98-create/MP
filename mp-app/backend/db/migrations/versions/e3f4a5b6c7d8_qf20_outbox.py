"""Transactional outbox and dead letters (phase 8, QF-20).

Events are written in the same transaction as the domain change; the relay
claims them exclusively and retries with backoff before dead-lettering.

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EVENTS = "outbox_events"
_DEAD = "outbox_dead_letters"


def upgrade() -> None:
    op.create_table(
        _EVENTS,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(length=60), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("dedup_key", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_outbox_events_dedup",
        _EVENTS,
        ["dedup_key"],
        unique=True,
        sqlite_where=sa.text("dedup_key IS NOT NULL"),
        postgresql_where=sa.text("dedup_key IS NOT NULL"),
    )
    op.create_index("ix_outbox_events_status_available", _EVENTS, ["status", "available_at"])

    op.create_table(
        _DEAD,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "outbox_id",
            sa.Integer(),
            sa.ForeignKey(f"{_EVENTS}.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("topic", sa.String(length=60), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_outbox_dead_letters_outbox_id", _DEAD, ["outbox_id"])


def downgrade() -> None:
    op.drop_index("ix_outbox_dead_letters_outbox_id", table_name=_DEAD)
    op.drop_table(_DEAD)
    op.drop_index("ix_outbox_events_status_available", table_name=_EVENTS)
    op.drop_index("uq_outbox_events_dedup", table_name=_EVENTS)
    op.drop_table(_EVENTS)

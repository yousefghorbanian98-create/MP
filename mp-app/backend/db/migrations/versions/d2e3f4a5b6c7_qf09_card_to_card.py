"""Card-to-card receipts: review queue, atomic approval, idempotency (phase 6).

`payments` gains three nullable columns (creator, plan to activate, idempotency
key) and a partial unique index on `(member_id, idempotency_key)`. The new
`payment_receipts` table stores only the private file path, never the bytes.

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d2e3f4a5b6c7"
down_revision: str | Sequence[str] | None = "c1d2e3f4a5b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_RECEIPTS = "payment_receipts"


def upgrade() -> None:
    # SQLite نمی‌تواند constraint را با ALTER اضافه کند؛ batch mode همان
    # «ساخت مجدد جدول» را برای هر دو موتور امن انجام می‌دهد.
    with op.batch_alter_table("payments") as batch:
        batch.add_column(sa.Column("created_by_user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("plan_key", sa.String(length=40), nullable=True))
        batch.add_column(sa.Column("idempotency_key", sa.String(length=64), nullable=True))
        batch.create_foreign_key(
            "fk_payments_created_by_user_id",
            "users",
            ["created_by_user_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "uq_payments_member_idempotency",
        "payments",
        ["member_id", "idempotency_key"],
        unique=True,
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
    )

    op.create_table(
        _RECEIPTS,
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "payment_id",
            sa.Integer(),
            sa.ForeignKey("payments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("review_id", sa.String(length=64), nullable=False),
        sa.Column("stored_path", sa.String(length=300), nullable=False),
        sa.Column("mime", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column(
            "uploaded_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="in_review"),
        sa.Column("reject_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "reviewed_by_user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_payment_receipts_payment_id", _RECEIPTS, ["payment_id"])
    op.create_index("uq_payment_receipts_review_id", _RECEIPTS, ["review_id"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_payment_receipts_review_id", table_name=_RECEIPTS)
    op.drop_index("ix_payment_receipts_payment_id", table_name=_RECEIPTS)
    op.drop_table(_RECEIPTS)
    op.drop_index("uq_payments_member_idempotency", table_name="payments")
    with op.batch_alter_table("payments") as batch:
        batch.drop_constraint("fk_payments_created_by_user_id", type_="foreignkey")
        batch.drop_column("idempotency_key")
        batch.drop_column("plan_key")
        batch.drop_column("created_by_user_id")

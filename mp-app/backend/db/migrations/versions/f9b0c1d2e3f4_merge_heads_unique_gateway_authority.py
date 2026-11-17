"""Merge current migration heads and enforce unique gateway authorities.

Revision ID: f9b0c1d2e3f4
Revises: d9e0f1a2b3c4, f1a2b3c4d5e6

The gateway authority is an idempotency key. Legacy non-gateway payments use
an empty value, so those values become NULL before a unique partial index is
created. Duplicate non-empty authorities are deliberately not rewritten: the
operator must investigate them before retrying this migration.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f9b0c1d2e3f4"
down_revision: str | Sequence[str] | None = ("d9e0f1a2b3c4", "f1a2b3c4d5e6")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_INDEX = "uq_payments_gateway_authority_nonnull"
_OLD_INDEX = "ix_payments_gateway_authority"


def upgrade() -> None:
    bind = op.get_bind()
    duplicate_authority_groups = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM (
                SELECT gateway_authority
                FROM payments
                WHERE gateway_authority IS NOT NULL AND gateway_authority <> ''
                GROUP BY gateway_authority
                HAVING COUNT(*) > 1
            ) AS duplicate_authorities
            """
        )
    ).scalar_one()
    if duplicate_authority_groups:
        raise RuntimeError(
            f"{duplicate_authority_groups} duplicate non-empty payment gateway authorities; "
            "investigate and reconcile them before upgrading"
        )

    bind.execute(
        sa.text("UPDATE payments SET gateway_authority = NULL WHERE gateway_authority = ''")
    )
    with op.batch_alter_table("payments") as batch:
        batch.drop_index(_OLD_INDEX)
        batch.alter_column(
            "gateway_authority",
            existing_type=sa.String(length=80),
            existing_nullable=False,
            existing_server_default=sa.text("''"),
            nullable=True,
            server_default=None,
        )
        batch.create_index(
            _INDEX,
            ["gateway_authority"],
            unique=True,
            sqlite_where=sa.text("gateway_authority IS NOT NULL"),
            postgresql_where=sa.text("gateway_authority IS NOT NULL"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("UPDATE payments SET gateway_authority = '' WHERE gateway_authority IS NULL")
    )
    with op.batch_alter_table("payments") as batch:
        batch.drop_index(_INDEX)
        batch.alter_column(
            "gateway_authority",
            existing_type=sa.String(length=80),
            existing_nullable=True,
            nullable=False,
            server_default=sa.text("''"),
        )
        batch.create_index(_OLD_INDEX, ["gateway_authority"], unique=False)

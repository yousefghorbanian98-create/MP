"""G2 — کوپن تخفیف (درصدی/مبلغ ثابت، انقضا، سقف استفاده) و ستون‌های تخفیف پرداخت.

Revision ID: a7c3d9e1f2b4
Revises: 632164e8c647
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a7c3d9e1f2b4"
down_revision: str | Sequence[str] | None = "632164e8c647"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "coupons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("kind", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("max_uses", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_coupons_created_at", "coupons", ["created_at"])
    with op.batch_alter_table("payments") as batch:
        batch.add_column(sa.Column("coupon_id", sa.Integer(), nullable=True))
        batch.add_column(
            sa.Column("discount_rial", sa.Integer(), server_default=sa.text("0"), nullable=False)
        )
        batch.create_index("ix_payments_coupon_id", ["coupon_id"])
        batch.create_foreign_key(
            "fk_payments_coupon_id", "coupons", ["coupon_id"], ["id"], ondelete="SET NULL"
        )


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch:
        batch.drop_constraint("fk_payments_coupon_id", type_="foreignkey")
        batch.drop_index("ix_payments_coupon_id")
        batch.drop_column("discount_rial")
        batch.drop_column("coupon_id")
    op.drop_index("ix_coupons_created_at", table_name="coupons")
    op.drop_table("coupons")

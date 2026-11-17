"""M27 — جدول‌های کلاس/رزرو + انتساب مربی به پرداخت (کمیسیون).

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a1"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gym_classes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("schedule_text", sa.String(200), nullable=False, server_default=""),
        sa.Column("branch_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "class_bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "class_id",
            sa.Integer(),
            sa.ForeignKey("gym_classes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "member_id",
            sa.Integer(),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(20), nullable=False, server_default="confirmed"),
        sa.Column("branch_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("class_id", "member_id", name="uq_class_member"),
    )
    with op.batch_alter_table("payments") as batch:
        batch.add_column(
            sa.Column(
                "coach_id",
                sa.Integer(),
                sa.ForeignKey("users.id", name="fk_payments_coach_id"),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("payments") as batch:
        batch.drop_column("coach_id")
    op.drop_table("class_bookings")
    op.drop_table("gym_classes")

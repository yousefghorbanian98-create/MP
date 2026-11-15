"""M38-c2 — جدول بازخورد ست‌به‌ست (set_feedbacks)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "e0f1a2b3c4d5"
down_revision = "c8d9e0f1a2b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "set_feedbacks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("member_id", sa.Integer(), sa.ForeignKey("members.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("program_id", sa.Integer(), sa.ForeignKey("workout_programs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("branch_id", sa.Integer(), nullable=False, server_default="1", index=True),
        sa.Column("movement_id", sa.String(length=60), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("target_reps", sa.Integer(), nullable=False),
        sa.Column("reps_done", sa.Integer(), nullable=False),
        sa.Column("rir", sa.Float(), nullable=True),
        sa.Column("soreness", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("set_feedbacks")

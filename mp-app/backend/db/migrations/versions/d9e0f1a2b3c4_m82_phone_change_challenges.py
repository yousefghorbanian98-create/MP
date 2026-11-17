"""M82 — persist short-lived dual-OTP phone-change challenges.

Revision ID: d9e0f1a2b3c4
Revises: c5d6e7f8a9b0
Create Date: 2026-11-16
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "d9e0f1a2b3c4"
down_revision = "c5d6e7f8a9b0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("auth_version", sa.Integer(), server_default="0", nullable=False)
    )
    op.create_table(
        "phone_change_challenges",
        sa.Column("challenge_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("old_phone", sa.String(length=15), nullable=False),
        sa.Column("new_phone", sa.String(length=15), nullable=False),
        sa.Column("old_code_hash", sa.String(length=128), nullable=False),
        sa.Column("new_code_hash", sa.String(length=128), nullable=True),
        sa.Column("old_attempts", sa.Integer(), nullable=False),
        sa.Column("new_attempts", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("old_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "old_attempts >= 0", name="ck_phone_change_challenges_old_attempts_nonnegative"
        ),
        sa.CheckConstraint(
            "new_attempts >= 0", name="ck_phone_change_challenges_new_attempts_nonnegative"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("challenge_id"),
    )
    op.create_index(
        "ix_phone_change_challenges_user_id", "phone_change_challenges", ["user_id"], unique=False
    )
    op.create_index(
        "ix_phone_change_challenges_expires_at",
        "phone_change_challenges",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_phone_change_challenges_expires_at", table_name="phone_change_challenges")
    op.drop_index("ix_phone_change_challenges_user_id", table_name="phone_change_challenges")
    op.drop_table("phone_change_challenges")
    op.drop_column("users", "auth_version")

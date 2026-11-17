"""M36-c1 — جدول‌های ارزیابی ۱۴ توانایی (axis_assessments/axis_scores/field_test_results)."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "b7c8d9e0f1a2"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "axis_assessments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "member_id",
            sa.Integer(),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("coach_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("branch_id", sa.Integer(), nullable=False, server_default="1", index=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("meta", sa.Text(), nullable=False, server_default="{}"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_table(
        "axis_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Integer(),
            sa.ForeignKey("axis_assessments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("axis", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("quality", sa.String(length=20), nullable=False, server_default="missing"),
        sa.Column("rule_version", sa.String(length=40), nullable=False, server_default=""),
        sa.UniqueConstraint("assessment_id", "axis", name="uq_axis_score"),
    )
    op.create_table(
        "field_test_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "assessment_id",
            sa.Integer(),
            sa.ForeignKey("axis_assessments.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("test_key", sa.String(length=40), nullable=False, index=True),
        sa.Column("raw_value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("percentile", sa.Float(), nullable=True),
        sa.Column("quality", sa.String(length=20), nullable=False, server_default=""),
        sa.Column("rule_version", sa.String(length=40), nullable=False, server_default=""),
        sa.Column("norm_source", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("measured_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_table("field_test_results")
    op.drop_table("axis_scores")
    op.drop_table("axis_assessments")

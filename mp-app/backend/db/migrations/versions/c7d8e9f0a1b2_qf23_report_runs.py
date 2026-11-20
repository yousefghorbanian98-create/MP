"""Scheduled report runs, one per (job, Tehran day) (phase 8 loop 3, QF-23).

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7d8e9f0a1b2"
down_revision: str | Sequence[str] | None = "b6c7d8e9f0a1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "report_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_key", sa.String(length=40), nullable=False),
        sa.Column("run_date", sa.Date(), nullable=False),
        sa.Column("payments_total_rial", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expenses_total_rial", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("net_rial", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payments_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expenses_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint("job_key", "run_date", name="uq_report_runs_job_day"),
    )
    op.create_index("ix_report_runs_job_key", "report_runs", ["job_key"])
    op.create_index("ix_report_runs_run_date", "report_runs", ["run_date"])


def downgrade() -> None:
    op.drop_index("ix_report_runs_run_date", table_name="report_runs")
    op.drop_index("ix_report_runs_job_key", table_name="report_runs")
    op.drop_table("report_runs")

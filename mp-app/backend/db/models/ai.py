"""مدل‌های ai_engine — لاگ اجرای موتور قواعد (بازتولیدپذیری/ردیابی)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class RuleRun(Base):
    """یک اجرای موتور قواعد — ورودی/خروجی کامل برای بازتولید و تست."""

    __tablename__ = "rule_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    program_id: Mapped[int | None] = mapped_column(
        ForeignKey("workout_programs.id", ondelete="SET NULL"), nullable=True
    )
    input_json: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[str] = mapped_column(Text, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

"""مدل‌های assessment — ارزیابی ۱۴ دامنه، نمرات دامنه، JP7."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, BranchMixin, TimestampMixin

# ۱۴ دامنهٔ آمادگی سلامت-عملکرد (شناسه‌های پایدار — نام‌ها در service)
DOMAIN_COUNT = 14


class Assessment14Domain(TimestampMixin, BranchMixin, Base):
    """یک جلسهٔ ارزیابی کامل برای عضو."""

    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    coach_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # پرچم‌های خطر به‌صورت JSON متنی (مثلاً '["cardio_red"]')
    flags: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    scores: Mapped[list[DomainScore]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class DomainScore(Base):
    """نمرهٔ یک دامنه (۱ تا ۱۴) داخل یک ارزیابی."""

    __tablename__ = "domain_scores"
    __table_args__ = (UniqueConstraint("assessment_id", "domain", name="uq_assessment_domain"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    domain: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..14
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..5
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    assessment: Mapped[Assessment14Domain] = relationship(back_populates="scores")


class JacksonPollockMeasurement(BranchMixin, Base):
    """اندازه‌گیری JP7 — ۷ چین پوستی + درصد چربی محاسبه‌شده."""

    __tablename__ = "jackson_pollock_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    # ۷ چین به‌صورت JSON متنی: '{"chest":12,"abdomen":15,...}'
    skinfolds_mm: Mapped[str] = mapped_column(Text, nullable=False)
    body_fat_pct: Mapped[float] = mapped_column(nullable=False)
    measured_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

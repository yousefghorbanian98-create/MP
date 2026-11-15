"""مدل‌های assessment — ارزیابی ۱۴ دامنه، نمرات دامنه، JP7."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
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
    # E07/D-012: تا تأیید مرجع مستقل، هیچ درصد چربی محاسبه/ذخیره نمی‌شود (None = نامعلوم)
    body_fat_pct: Mapped[float | None] = mapped_column(nullable=True)
    equation_version: Mapped[str] = mapped_column(
        String(64), nullable=False, default="LOCKED:pending-independent-reference"
    )
    quality: Mapped[str | None] = mapped_column(String(32), nullable=True)  # E02: کیفیت اندازه‌گیری
    method: Mapped[str | None] = mapped_column(String(64), nullable=True)  # E02: روش/ابزار
    measured_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class NormEntry(TimestampMixin, Base):
    """ردیف نُرم یک آزمون میدانی (M35-c1) — صدکی یا معیاری، همیشه با منبع (E13)."""

    __tablename__ = "norm_entries"
    __table_args__ = (
        UniqueConstraint("test_key", "sex", "age_min", "age_max", name="uq_norm_test_sex_age"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    test_key: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name_fa: Mapped[str] = mapped_column(String(120), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)  # reps | cm | sec | ...
    # percentile: جدول صدکی واقعی | criterion: باند معیاری (candidate تا منبع مستقل)
    method: Mapped[str] = mapped_column(String(20), nullable=False, default="percentile")
    sex: Mapped[str] = mapped_column(String(10), nullable=False)  # m | f | all
    age_min: Mapped[int] = mapped_column(Integer, nullable=False)
    age_max: Mapped[int] = mapped_column(Integer, nullable=False)
    # JSON: {"5": x, "25": y, "50": z, "75": w, "95": v} — ممکن است ناقص باشد (quality در امتیازدهی)
    percentiles: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    # JSON باندهای معیاری برای method=criterion
    bands: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    # higher_better | lower_better (مثلاً زمان دویدن: کمتر بهتر)
    direction: Mapped[str] = mapped_column(String(20), default="higher_better", nullable=False)
    # کوچک‌ترین تغییر واقعی (SDC) — گیت «تغییر واقعی» در امتیازدهی مجدد
    sdc: Mapped[float | None] = mapped_column(Float, nullable=True)
    sdc_note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    source: Mapped[str] = mapped_column(String(300), nullable=False)
    source_version: Mapped[str] = mapped_column(String(60), default="", nullable=False)


class AxisAssessment(TimestampMixin, BranchMixin, Base):
    """جلسهٔ ارزیابی ۱۴ توانایی (M36) — درصد محورها از آزمون‌های میدانی."""

    __tablename__ = "axis_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    coach_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="draft", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # JSON: متادیتای جلسه (نسخهٔ قواعد، شرایط، ...) — E02
    meta: Mapped[str] = mapped_column(Text, default="{}", nullable=False)

    scores: Mapped[list[AxisScore]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )
    tests: Mapped[list[FieldTestResult]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class AxisScore(Base):
    """نمرهٔ درصدی یک محور (۰..۱۰۰) + کیفیت — نمرهٔ نامعلوم = missing، هرگز صفر."""

    __tablename__ = "axis_scores"
    __table_args__ = (UniqueConstraint("assessment_id", "axis", name="uq_axis_score"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("axis_assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    axis: Mapped[int] = mapped_column(Integer, nullable=False)  # 1..14
    score: Mapped[float | None] = mapped_column(Float, nullable=True)  # None = missing
    quality: Mapped[str] = mapped_column(String(20), default="missing", nullable=False)
    # نسخهٔ قاعدهٔ نگاشت آزمون←محور (AXIS_TEST_MAP)
    rule_version: Mapped[str] = mapped_column(String(40), default="", nullable=False)

    assessment: Mapped[AxisAssessment] = relationship(back_populates="scores")


class FieldTestResult(Base):
    """نتیجهٔ خام یک آزمون میدانی + درصدک برآوردشده (M36)."""

    __tablename__ = "field_test_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("axis_assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    test_key: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    percentile: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    # نسخهٔ موتور امتیازدهی + منبع نُرم (E13)
    rule_version: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    norm_source: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    measured_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    assessment: Mapped[AxisAssessment] = relationship(back_populates="tests")

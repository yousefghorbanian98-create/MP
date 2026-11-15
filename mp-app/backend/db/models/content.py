"""مدل‌های content — کتابخانهٔ حرکات و غذاها (seed محلی + منابع خارجی)."""

from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, TimestampMixin


class Exercise(TimestampMixin, Base):
    """حرکت ورزشی — همگام با wger یا seed دستی."""

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(40), default="", nullable=False, index=True)
    name_fa: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    equipment: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="intermediate", nullable=False)
    # حرکات جایگزین/ممنوع برای محدودیت‌ها — JSON متنی
    contraindications: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    video_url: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    instructions_fa: Mapped[str] = mapped_column(Text, default="", nullable=False)


class CatalogSource(TimestampMixin, Base):
    """منبع خارجیِ کاتالوگ حرکات (E12 — پیش از هر ادغام ثبت می‌شود)."""

    __tablename__ = "catalog_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    upstream_url: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    upstream_commit: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    license: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    # sha256 فایل دادهٔ ورودی — ردیابی یکپارچگی (بدون دادهٔ واقعی کاربران)
    digest: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    exercise_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CatalogExercise(TimestampMixin, Base):
    """حرکت واردشده از کاتالوگ خارجی — بدون برچسب محوری (از M33-c3)."""

    __tablename__ = "catalog_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    force: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    mechanic: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    equipment: Mapped[str] = mapped_column(String(40), default="", nullable=False)
    # JSON متنی — فهرست‌ها (E02: بدون نرمال‌سازی زیادی)
    primary_muscles: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    secondary_muscles: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    instructions: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    image_refs: Mapped[str] = mapped_column(Text, default="[]", nullable=False)


class FoodItem(TimestampMixin, Base):
    """مادهٔ غذایی — همگام با Open Food Facts/USDA یا جدول ایرانی دستی."""

    __tablename__ = "food_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    external_id: Mapped[str] = mapped_column(String(40), default="", nullable=False, index=True)
    name_fa: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    kcal_per_100g: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_g_per_100g: Mapped[float] = mapped_column(nullable=False, default=0)
    carbs_g_per_100g: Mapped[float] = mapped_column(nullable=False, default=0)
    fat_g_per_100g: Mapped[float] = mapped_column(nullable=False, default=0)
    category: Mapped[str] = mapped_column(String(40), default="", nullable=False)

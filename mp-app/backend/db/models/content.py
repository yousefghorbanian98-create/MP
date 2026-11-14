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

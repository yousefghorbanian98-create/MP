"""مدل‌های nutrition — برنامهٔ تغذیه وعده‌ها."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, BranchMixin, TimestampMixin


class NutritionPlan(TimestampMixin, BranchMixin, Base):
    """برنامهٔ تغذیه — خروجی موتور قواعد + تأیید مربی (همان گردش برنامهٔ تمرین)."""

    __tablename__ = "nutrition_plans"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    coach_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )  # draft | approved | rejected
    daily_kcal: Mapped[int] = mapped_column(Integer, nullable=False)
    protein_g: Mapped[int] = mapped_column(Integer, nullable=False)
    carbs_g: Mapped[int] = mapped_column(Integer, nullable=False)
    fat_g: Mapped[int] = mapped_column(Integer, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(20), default="", nullable=False)
    llm_explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)

    meals: Mapped[list[MealItem]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class MealItem(Base):
    """یک آیتم غذایی در یک وعده."""

    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("nutrition_plans.id", ondelete="CASCADE"), index=True, nullable=False
    )
    food_id: Mapped[int] = mapped_column(ForeignKey("food_items.id", ondelete="RESTRICT"))
    meal_slot: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # breakfast|lunch|dinner|snack
    grams: Mapped[int] = mapped_column(Integer, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    plan: Mapped[NutritionPlan] = relationship(back_populates="meals")

"""مدل‌های membership — عضو، پروفایل، اشتراک."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base, BranchMixin, TimestampMixin


class Member(TimestampMixin, BranchMixin, Base):
    """پروفایل عضو — ورودی موتور قواعد از اینجاست (هدف/محدودیت/ابعاد)."""

    __tablename__ = "members"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), default="unknown", nullable=False)
    height_cm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goal: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    # محدودیت‌ها/آسیب‌ها به‌صورت JSON متنی (مثلاً '["knee_pain"]') — ورودی قید موتور قواعد
    constraints: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    emergency_contact: Mapped[str] = mapped_column(String(120), default="", nullable=False)

    user: Mapped[User] = relationship(back_populates="member")  # noqa: F821
    memberships: Mapped[list[Membership]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )


class Membership(BranchMixin, Base):
    """اشتراک باشگاه (پلن + بازه + وضعیت)."""

    __tablename__ = "memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_name: Mapped[str] = mapped_column(String(60), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, index=True
    )  # active | expired | cancelled
    price_rial: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    member: Mapped[Member] = relationship(back_populates="memberships")

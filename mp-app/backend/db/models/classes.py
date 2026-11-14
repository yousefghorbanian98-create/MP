"""مدل‌های کلاس گروهی و رزرو (M27)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, BranchMixin, TimestampMixin


class GymClass(TimestampMixin, BranchMixin, Base):
    """کلاس گروهی باشگاه."""

    __tablename__ = "gym_classes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    coach_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    schedule_text: Mapped[str] = mapped_column(String(200), default="", nullable=False)


class ClassBooking(TimestampMixin, BranchMixin, Base):
    """رزرو کلاس — confirmed یا waitlisted (به ترتیب زمانی)."""

    __tablename__ = "class_bookings"
    __table_args__ = (UniqueConstraint("class_id", "member_id", name="uq_class_member"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey("gym_classes.id", ondelete="CASCADE"), index=True, nullable=False
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="confirmed"
    )  # confirmed|waitlisted|cancelled
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

"""اندازه‌گیری محیط اندام برای آنالیز سگمنتال (M54-c1 / D-024).

## چرا این جدول، و چه چیزی **نیست**
D-024 صریح است: «آنالیز سگمنتال با مسیر نرم‌افزاریِ بدون سخت‌افزار — نه
ادعای InBody». پس اینجا هیچ ادعای امپدانس/ترکیب بدنی نمی‌کنیم. فقط
**محیط‌های آنتروپومتریک** را ثبت می‌کنیم: چیزی که مربی با متر می‌گیرد.

هر محیط اختیاری است چون اندازه‌گیری کامل در یک جلسه واقع‌بینانه نیست.
`None` یعنی «اندازه‌گیری نشده» — با صفر پر نمی‌شود (قاعدهٔ کل پروژه).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, BranchMixin


class LimbMeasurement(BranchMixin, Base):
    """یک اندازه‌گیری محیط اندام در یک لحظه.

    واحد: سانتی‌متر، مضرب ۰٫۱. سمت (`side`) برای اندام‌های زوجی مهم است:
    عدم تقارن چپ/راست یک یافتهٔ واقعی است، ولی فقط اگر دو بار گرفته شود.
    """

    __tablename__ = "limb_measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    measured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False, index=True
    )

    # محیط‌ها (cm) — همه اختیاری
    neck_cm: Mapped[float | None] = mapped_column(nullable=True)
    chest_cm: Mapped[float | None] = mapped_column(nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(nullable=True)
    hip_cm: Mapped[float | None] = mapped_column(nullable=True)
    upper_arm_right_cm: Mapped[float | None] = mapped_column(nullable=True)
    upper_arm_left_cm: Mapped[float | None] = mapped_column(nullable=True)
    thigh_right_cm: Mapped[float | None] = mapped_column(nullable=True)
    thigh_left_cm: Mapped[float | None] = mapped_column(nullable=True)
    calf_right_cm: Mapped[float | None] = mapped_column(nullable=True)
    calf_left_cm: Mapped[float | None] = mapped_column(nullable=True)

    measured_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    quality: Mapped[str | None] = mapped_column(String(32), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

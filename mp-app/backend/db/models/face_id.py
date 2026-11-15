"""مدل‌های face_id — چهره (رمزنگاری‌شده)، رضایت‌نامه، چک‌این."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, BranchMixin


class FaceTemplate(BranchMixin, Base):
    """قالب چهره — فقط embedding رمزنگاری‌شده با PyNaCl (ADR-004 / NFR-3).

    هرگز تصویر خام یا embedding خام ذخیره نمی‌شود.
    """

    __tablename__ = "face_templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    embedding_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(30), default="sface-v1", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class BiometricConsent(Base):
    """رضایت‌نامهٔ بیومتریک — رضایت صریح، قابل پس‌گرفتن (حق حذف)."""

    __tablename__ = "biometric_consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    policy_version: Mapped[str] = mapped_column(String(20), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class CheckIn(BranchMixin, Base):
    """چک‌این ورود به باشگاه (qr | face | manual)."""

    __tablename__ = "checkins"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    method: Mapped[str] = mapped_column(String(10), nullable=False)  # qr | face | manual
    result: Mapped[str] = mapped_column(String(10), default="ok", nullable=False)  # ok | denied
    denial_reason: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    # M42-c2: ثبت خروج — طول جلسه = checked_out_at − created_at (نامعلوم تا ثبت خروج)
    checked_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

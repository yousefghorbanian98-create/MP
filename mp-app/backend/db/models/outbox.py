"""مدل‌های outbox — رویداد تراکنشی، dead-letter و رد ارسال (QF-20).

قاعدهٔ طراحی: رویداد در همان تراکنشِ عملیات دامنه ساخته می‌شود؛ پس هیچ
«پول ثبت شد ولی رویدادش گم شد» نداریم. ارسال at-least-once است، بنابراین
consumer باید idempotent باشد (`dedup_key`).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class OutboxEvent(Base):
    """رویداد صف — وضعیت: pending | sending | sent | dead."""

    __tablename__ = "outbox_events"
    __table_args__ = (
        Index(
            "uq_outbox_events_dedup",
            "dedup_key",
            unique=True,
            sqlite_where=text("dedup_key IS NOT NULL"),
            postgresql_where=text("dedup_key IS NOT NULL"),
        ),
        Index("ix_outbox_events_status_available", "status", "available_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(60), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    dedup_key: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OutboxDeadLetter(Base):
    """رد ارسال — علت و تلاش‌ها برای بررسی انسانی نگه داشته می‌شود."""

    __tablename__ = "outbox_dead_letters"

    id: Mapped[int] = mapped_column(primary_key=True)
    outbox_id: Mapped[int] = mapped_column(
        ForeignKey("outbox_events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(60), nullable=False)
    payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )


class InboxMessage(Base):
    """پیام مصرف‌شده — کلید `(topic, dedup_key)` یکتا، اثر handler یک‌بار.

    ردیف در همان تراکنشِ اثر ساخته می‌شود؛ اگر handler خطا بدهد، هم اثر و هم
    ردیف rollback می‌شوند و retry بعدی مجاز است.
    """

    __tablename__ = "inbox_messages"
    __table_args__ = (Index("uq_inbox_messages_topic_key", "topic", "dedup_key", unique=True),)

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str] = mapped_column(String(60), nullable=False)
    dedup_key: Mapped[str] = mapped_column(String(120), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )

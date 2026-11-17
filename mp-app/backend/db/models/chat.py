"""مدل‌های چت مربی–شاگرد (G8).

تفاوت با `Notification`: اعلان یک‌طرفه و بدون پاسخ است؛ پیام، **گفتگو**ست
و طرف مقابل می‌تواند پاسخ دهد. جعل یکی به‌جای دیگری، هم UX را خراب می‌کند
و هم در سند دفاعی قابل دفاع نیست.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, BranchMixin, TimestampMixin


class Conversation(TimestampMixin, BranchMixin, Base):
    """یک گفتگو بین یک عضو و یک مربی.

    `member_id` + `coach_id` یکتا نیستند: ممکن است مربی عوض شود و سابقه
    باید بماند. گفتگو با `status` بسته می‌شود، نه با حذف.
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    coach_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    subject: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="open", nullable=False, index=True
    )  # open | closed
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class Message(TimestampMixin, Base):
    """یک پیام در گفتگو.

    `read_at` عمداً nullable است: «خوانده نشده» یک حالت واقعی است و با
    صفر/تاریخ ساختگی پر نمی‌شود.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    sender_role: Mapped[str] = mapped_column(String(20), nullable=False)  # member | coach
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # پیام سیستمی (مثلاً «برنامه تأیید شد») با فرستندهٔ None ساخته نمی‌شود؛
    # به‌جایش پرچم صریح است تا ادمین بتواند فیلتر کند.
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

"""سرویس notification — اعلان‌ها."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from db.models import Member, Notification


def send(
    db: Session, member_id: int, title: str, body: str = "", kind: str = "general"
) -> Notification:
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    n = Notification(member_id=member_id, title=title, body=body, kind=kind)
    db.add(n)
    db.commit()
    db.refresh(n)
    return n


def list_member_notifications(
    db: Session, member_id: int, unread_only: bool = False
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.member_id == member_id)
        .order_by(Notification.id.desc())
    )
    if unread_only:
        stmt = stmt.where(Notification.read_at.is_(None))
    return list(db.scalars(stmt))


def mark_read(db: Session, notification_id: int) -> Notification:
    n = db.get(Notification, notification_id)
    if n is None:
        raise NotFoundError("اعلان یافت نشد")
    if n.read_at is None:
        n.read_at = datetime.now(UTC)
        db.commit()
        db.refresh(n)
    return n

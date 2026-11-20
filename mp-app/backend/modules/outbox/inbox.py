"""inbox — تحویل at-least-once را به اثر «یک‌بار» تبدیل می‌کند (QF-21).

الگو: `INSERT` ردیف پیام در همان تراکنشِ اثر. اگر کلید تکراری باشد،
`IntegrityError` می‌گیریم و handler اجرا نمی‌شود. هیچ ادعای exactly-once در
لایهٔ انتقال نداریم؛ ادعا فقط در سطح «اثر» است.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.errors import ApiError
from db.models import InboxMessage


def consume_once(
    db: Session,
    *,
    topic: str,
    dedup_key: str,
    handler: Callable[[], None],
    commit: bool = True,
) -> dict:
    """اثر handler را یک‌بار اجرا می‌کند؛ بار دوم `duplicate` برمی‌گردد."""
    if not dedup_key:
        raise ApiError("dedup_key برای مصرف امن الزامی است", code="missing_dedup_key")
    existing = db.scalar(
        select(InboxMessage.id).where(
            InboxMessage.topic == topic, InboxMessage.dedup_key == dedup_key
        )
    )
    if existing is not None:
        return {"status": "duplicate", "inbox_id": existing}

    message = InboxMessage(topic=topic, dedup_key=dedup_key, processed_at=datetime.now(UTC))
    db.add(message)
    try:
        db.flush()
    except IntegrityError:
        # رقابت دو consumer روی همان کلید: یکی برنده است، دیگری duplicate.
        db.rollback()
        existing = db.scalar(
            select(InboxMessage.id).where(
                InboxMessage.topic == topic, InboxMessage.dedup_key == dedup_key
            )
        )
        return {"status": "duplicate", "inbox_id": existing}

    handler()
    if commit:
        db.commit()
        db.refresh(message)
    else:
        db.flush()
    return {"status": "consumed", "inbox_id": message.id}


def inbox_count(db: Session, topic: str | None = None) -> int:
    stmt = select(InboxMessage.id)
    if topic:
        stmt = stmt.where(InboxMessage.topic == topic)
    return len(list(db.scalars(stmt)))

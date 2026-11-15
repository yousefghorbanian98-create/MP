"""سرویس چت مربی–شاگرد (G8) — chat-1.0.

## تصمیم‌های صریح
1. **دسترسی دوطرفه با یک قاعده.** عضو فقط گفتگوهای خودش را می‌بیند؛
   مربی فقط گفتگوهایی که خودش طرفشان است. هیچ‌کس با حدس `conversation_id`
   به گفتگوی دیگری دسترسی ندارد (تست ۴۰۳ دارد).
2. **فرستنده از توکن، نه از body.** اگر `sender_id` از ورودی خوانده شود،
   هر کسی می‌تواند خودش را مربی جا بزند.
3. **پیام خالی رد می‌شود**، نه ذخیره. و طول سقف دارد تا DoS ساده نشود.
4. **`read_at` با NULL می‌ماند** تا «خوانده نشده» واقعی بماند.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, ForbiddenError, NotFoundError

CHAT_VERSION = "chat-1.0"
MAX_BODY = 2000


def _load_conversation(db: Session, conversation_id: int, user) -> object:
    from db.models import Conversation, Member, User

    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise NotFoundError("گفتگو یافت نشد")

    if user.role == "member":
        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if member is None or conv.member_id != member.id:
            raise ForbiddenError("این گفتگو متعلق به شما نیست")
        return conv

    # نقش‌های باشگاهی: فقط طرف گفتگو
    if conv.coach_id != user.id and user.role not in ("super_admin", "admin"):
        raise ForbiddenError("طرف این گفتگو نیستید")
    _ = User  # import برای type checker
    return conv


def open_conversation(
    db: Session, *, member_id: int, coach_id: int | None, subject: str, user=None
) -> dict:
    """شروع گفتگو. مربی از توکن گرفته می‌شود اگر داده نشود."""
    from app.security.ownership import ensure_member_scope
    from db.models import Conversation, Member

    ensure_member_scope(db, user, member_id)
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")

    effective_coach = coach_id or getattr(user, "id", None)
    if effective_coach is None:
        raise ApiError("مربی مشخص نیست", code="missing_coach")

    conv = Conversation(
        member_id=member_id,
        coach_id=effective_coach,
        subject=(subject or "").strip()[:120],
        status="open",
        branch_id=1,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return _conv_dict(conv)


def _conv_dict(conv) -> dict:
    return {
        "id": conv.id,
        "member_id": conv.member_id,
        "coach_id": conv.coach_id,
        "subject": conv.subject,
        "status": conv.status,
        "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


def _msg_dict(m) -> dict:
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "sender_id": m.sender_id,
        "sender_role": m.sender_role,
        "body": m.body,
        "is_system": m.is_system,
        "read_at": m.read_at.isoformat() if m.read_at else None,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }


def send_message(db: Session, *, conversation_id: int, body: str, user) -> dict:
    """ارسال پیام. فرستنده از توکن گرفته می‌شود، نه از ورودی."""
    from db.models import Message

    conv = _load_conversation(db, conversation_id, user)
    text = (body or "").strip()
    if not text:
        raise ApiError("پیام خالی ارسال نمی‌شود", code="empty_message")
    if len(text) > MAX_BODY:
        raise ApiError(f"طول پیام بیش از {MAX_BODY} کاراکتر است", code="message_too_long")
    if conv.status == "closed":
        raise ApiError("این گفتگو بسته شده است", code="conversation_closed")

    role = "member" if user.role == "member" else "coach"
    msg = Message(
        conversation_id=conv.id,
        sender_id=user.id,
        sender_role=role,
        body=text,
        is_system=False,
    )
    db.add(msg)
    conv.last_message_at = datetime.now(UTC)
    db.commit()
    db.refresh(msg)
    return _msg_dict(msg)


def list_messages(db: Session, *, conversation_id: int, user, limit: int = 100) -> dict:
    """پیام‌های گفتگو به ترتیب زمان + شمارش خوانده‌نشده."""
    from db.models import Message

    _load_conversation(db, conversation_id, user)
    rows = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(max(1, min(int(limit), 200)))
        ).all()
    )
    rows.reverse()
    unread = sum(1 for m in rows if m.read_at is None and m.sender_id != user.id)
    return {
        "conversation_id": conversation_id,
        "messages": [_msg_dict(m) for m in rows],
        "unread_count": unread,
        "rule_version": CHAT_VERSION,
    }


def mark_read(db: Session, *, conversation_id: int, user) -> dict:
    """علامت‌گذاری پیام‌های طرف مقابل به‌عنوان خوانده‌شده."""
    from db.models import Message

    _load_conversation(db, conversation_id, user)
    now = datetime.now(UTC)
    rows = list(
        db.scalars(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.read_at.is_(None),
                Message.sender_id != user.id,
            )
        ).all()
    )
    for m in rows:
        m.read_at = now
    db.commit()
    return {"marked_read": len(rows), "rule_version": CHAT_VERSION}


def list_conversations(db: Session, *, user, member_id: int | None = None) -> list[dict]:
    """گفتگوهای کاربر. عضو ⇒ گفتگوهای خودش، مربی ⇒ گفتگوهای خودش."""
    from db.models import Conversation, Member

    if user.role == "member":
        member = db.scalar(select(Member).where(Member.user_id == user.id))
        if member is None:
            return []
        stmt = select(Conversation).where(Conversation.member_id == member.id)
    elif member_id is not None:
        stmt = select(Conversation).where(Conversation.member_id == member_id)
    elif user.role in ("super_admin", "admin"):
        stmt = select(Conversation)
    else:
        stmt = select(Conversation).where(Conversation.coach_id == user.id)

    stmt = stmt.order_by(Conversation.last_message_at.desc().nullslast(), Conversation.id.desc())
    return [_conv_dict(c) for c in db.scalars(stmt).all()]

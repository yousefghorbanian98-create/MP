"""روتر چت مربی–شاگرد (G8)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import CurrentUser, DbSession, require_permission
from modules.notification import chat_service

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_permission())])


class ConversationIn(BaseModel):
    member_id: int = Field(ge=1)
    coach_id: int | None = None
    subject: str = Field(default="", max_length=120)


class MessageIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


@router.get("/conversations", summary="گفتگوهای من (عضو یا مربی)")
def list_conversations(db: DbSession, user: CurrentUser, member_id: int | None = None):
    return chat_service.list_conversations(db, user=user, member_id=member_id)


@router.post("/conversations", summary="شروع گفتگوی جدید")
def open_conversation(payload: ConversationIn, db: DbSession, user: CurrentUser):
    return chat_service.open_conversation(
        db,
        member_id=payload.member_id,
        coach_id=payload.coach_id,
        subject=payload.subject,
        user=user,
    )


@router.get("/conversations/{conversation_id}/messages", summary="پیام‌های گفتگو")
def list_messages(conversation_id: int, db: DbSession, user: CurrentUser, limit: int = 100):
    return chat_service.list_messages(db, conversation_id=conversation_id, user=user, limit=limit)


@router.post("/conversations/{conversation_id}/messages", summary="ارسال پیام")
def send_message(conversation_id: int, payload: MessageIn, db: DbSession, user: CurrentUser):
    return chat_service.send_message(
        db, conversation_id=conversation_id, body=payload.body, user=user
    )


@router.post("/conversations/{conversation_id}/read", summary="علامت‌گذاری خوانده‌شده")
def mark_read(conversation_id: int, db: DbSession, user: CurrentUser):
    return chat_service.mark_read(db, conversation_id=conversation_id, user=user)

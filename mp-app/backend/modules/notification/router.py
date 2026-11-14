"""روتر notification."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.deps import DbSession
from modules.notification import service
from modules.notification.schemas import NotificationOut, NotificationSend

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=NotificationOut, summary="ارسال اعلان (US-107)")
def send(payload: NotificationSend, db: DbSession):
    return service.send(db, payload.member_id, payload.title, payload.body, payload.kind)


@router.get("/member/{member_id}", response_model=list[NotificationOut], summary="اعلان‌های عضو")
def list_notifications(member_id: int, db: DbSession, unread_only: bool = Query(False)):
    return service.list_member_notifications(db, member_id, unread_only)


@router.post("/{notification_id}/read", response_model=NotificationOut, summary="خواندن اعلان")
def mark_read(notification_id: int, db: DbSession):
    return service.mark_read(db, notification_id)

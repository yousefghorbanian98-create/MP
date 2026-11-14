"""اسکیمای notification."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NotificationSend(BaseModel):
    member_id: int
    title: str = Field(..., min_length=1, max_length=120)
    body: str = Field("", max_length=2000)
    kind: str = Field("general", pattern="^(renewal|workout|reassessment|general)$")


class NotificationOut(BaseModel):
    id: int
    member_id: int
    channel: str
    title: str
    body: str
    kind: str
    read_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}

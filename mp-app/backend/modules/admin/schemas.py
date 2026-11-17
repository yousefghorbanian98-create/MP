"""اسکیمای admin."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AuditOut(BaseModel):
    id: int
    actor_user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FeatureFlagIn(BaseModel):
    key: str = Field(..., min_length=2, max_length=60, pattern="^[a-z0-9_.-]+$")
    enabled: bool
    description: str = Field("", max_length=200)


class FeatureFlagOut(BaseModel):
    id: int
    key: str
    enabled: bool
    description: str

    model_config = {"from_attributes": True}

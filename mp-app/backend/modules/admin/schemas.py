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


class PermissionGrantIn(BaseModel):
    user_id: int = Field(..., ge=1)
    permission: str = Field(..., min_length=3, max_length=40)
    expires_in_hours: int | None = Field(None, ge=1, le=24 * 365)
    note: str = Field("", max_length=200)


class PermissionGrantOut(BaseModel):
    id: int
    user_id: int
    permission: str
    note: str
    granted_by: int | None
    granted_at: str | None
    expires_at: str | None
    revoked_at: str | None
    revoked_by: int | None
    active: bool
    status: str

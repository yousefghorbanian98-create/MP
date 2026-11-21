"""اسکیمای face_id."""

from __future__ import annotations

import base64
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.ids import Id


class ConsentIn(BaseModel):
    member_id: Id
    policy_version: str = Field("v1", max_length=20)


class ConsentOut(BaseModel):
    id: int
    member_id: int
    policy_version: str
    granted_at: datetime
    revoked_at: datetime | None

    model_config = {"from_attributes": True}


class FaceEnroll(BaseModel):
    member_id: Id
    embedding_b64: str = Field(..., description="embedding خروجی SFace (base64) — تصویر خام هرگز")

    @field_validator("embedding_b64")
    @classmethod
    def decode(cls, v: str) -> str:
        try:
            base64.b64decode(v, validate=True)
        except Exception as exc:
            raise ValueError("base64 معتبر نیست") from exc
        return v


class FaceTemplateOut(BaseModel):
    id: int
    member_id: int
    algorithm: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckInIn(BaseModel):
    member_id: Id
    method: str = Field(..., pattern="^(qr|face|manual)$")


class CheckInQrIn(BaseModel):
    """توکن QR به‌عنوان payload؛ بدون پذیرش object آزاد یا دادهٔ عضو دیگر."""

    payload: str = Field(..., min_length=1, max_length=4096)


class CheckInOut(BaseModel):
    id: int
    member_id: int
    method: str
    result: str
    denial_reason: str
    created_at: datetime

    model_config = {"from_attributes": True}

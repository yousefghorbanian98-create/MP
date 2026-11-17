"""سرویس admin — audit log، feature flags."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import NotFoundError
from db.models import AuditLog, FeatureFlag


def audit(
    db: Session,
    actor_user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    detail: dict | None = None,
    *,
    commit: bool = True,
) -> AuditLog:
    """ثبت عملیات حساس — فقط insert (غیرقابل‌حذف)."""
    row = AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        detail=json.dumps(detail or {}, ensure_ascii=False),
    )
    db.add(row)
    db.flush()
    if commit:
        db.commit()
        db.refresh(row)
    return row


def list_audit(db: Session, action: str | None = None, limit: int = 100) -> list[AuditLog]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    return list(db.scalars(stmt))


def list_flags(db: Session) -> list[FeatureFlag]:
    """همهٔ پرچم‌ها (M46-c1). لیست خالی = هیچ پرچمی تعریف نشده، نه ۴۰۴."""
    return list(db.scalars(select(FeatureFlag).order_by(FeatureFlag.key)))


def get_flag(db: Session, key: str) -> FeatureFlag:
    flag = db.scalar(select(FeatureFlag).where(FeatureFlag.key == key))
    if flag is None:
        raise NotFoundError("flag یافت نشد")
    return flag


def set_flag(
    db: Session,
    key: str,
    enabled: bool,
    description: str = "",
    actor_user_id: int | None = None,
) -> FeatureFlag:
    flag = db.scalar(select(FeatureFlag).where(FeatureFlag.key == key))
    previous_enabled: bool | None = None
    if flag is None:
        flag = FeatureFlag(key=key, enabled=enabled, description=description)
        db.add(flag)
    else:
        previous_enabled = flag.enabled
        flag.enabled = enabled
        if description:
            flag.description = description
    db.flush()
    # `audit` commits both the flag mutation and its audit row in one transaction.
    audit(
        db,
        actor_user_id,
        "feature_flag_updated",
        "feature_flag",
        flag.id,
        {"key": key, "enabled": enabled, "previous_enabled": previous_enabled},
    )
    db.refresh(flag)
    return flag


def is_enabled(db: Session, key: str, default: bool = False) -> bool:
    flag = db.scalar(select(FeatureFlag).where(FeatureFlag.key == key))
    return flag.enabled if flag is not None else default

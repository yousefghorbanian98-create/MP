"""سرویس مجوز شخصی ادمین (QF-03) — اعطا/سلب/فهرست، فقط مالک سیستم.

هر ردیف با `granted_by` و audit ثبت می‌شود؛ سلب، ردیف را حذف نمی‌کند.
مالک سیستم نیاز به ردیف ندارد (همیشه مجاز است) و برایش مجوز ساخته نمی‌شود؛
همچنین مجوز به خودِ مالک از طرف خودش معنا ندارد.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, ForbiddenError, NotFoundError
from app.security.grants import KNOWN_PERMISSIONS, effective_status
from db.models import AdminPermission, User
from modules.admin.service import audit


def _require_owner(actor: User) -> None:
    if actor.role != "super_admin":
        raise ForbiddenError("فقط مالک سیستم (super_admin) مجوز شخصی می‌دهد")


def _serialize(db: Session, row: AdminPermission, now: datetime) -> dict:
    status = effective_status(db, row.user_id, row.permission, now)
    return {
        "id": row.id,
        "user_id": row.user_id,
        "permission": row.permission,
        "note": row.note or "",
        "granted_by": row.granted_by,
        "granted_at": row.created_at.isoformat() if row.created_at else None,
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        "revoked_by": row.revoked_by,
        "active": row.revoked_at is None
        and (row.expires_at is None or _aware(row.expires_at) > now)
        and status == "active",
        "status": "revoked" if row.revoked_at else ("active" if status == "active" else "expired"),
    }


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def list_grants(db: Session, *, actor: User, user_id: int) -> list[dict]:
    _require_owner(actor)
    now = datetime.now(UTC)
    rows = db.scalars(
        select(AdminPermission)
        .where(AdminPermission.user_id == user_id)
        .order_by(AdminPermission.id.desc())
    )
    return [_serialize(db, row, now) for row in rows]


def list_known_permissions() -> list[dict]:
    return [{"key": key, "description": desc} for key, desc in KNOWN_PERMISSIONS.items()]


def grant(
    db: Session,
    *,
    actor: User,
    user_id: int,
    permission: str,
    expires_in_hours: int | None = None,
    note: str = "",
) -> dict:
    _require_owner(actor)
    if permission not in KNOWN_PERMISSIONS:
        raise ApiError(f"مجوز «{permission}» شناخته نیست", code="unknown_permission")
    target = db.get(User, user_id)
    if target is None:
        raise NotFoundError("کاربر یافت نشد")
    if target.role == "super_admin":
        raise ApiError("مالک سیستم به مجوز شخصی نیاز ندارد", code="owner_needs_no_permission")
    if expires_in_hours is not None and not (1 <= expires_in_hours <= 24 * 365):
        raise ApiError("مدت مجوز باید بین ۱ ساعت و ۱ سال باشد", code="invalid_expiry")

    now = datetime.now(UTC)
    row = AdminPermission(
        user_id=user_id,
        permission=permission,
        granted_by=actor.id,
        note=note,
        expires_at=None if expires_in_hours is None else now + timedelta(hours=expires_in_hours),
        created_at=now,
    )
    db.add(row)
    db.flush()
    audit(
        db,
        actor.id,
        "permission_grant",
        "user",
        user_id,
        {"grant_id": row.id, "permission": permission, "expires_in_hours": expires_in_hours},
        commit=False,
    )
    db.commit()
    db.refresh(row)
    return _serialize(db, row, now)


def revoke(db: Session, *, actor: User, grant_id: int) -> dict:
    _require_owner(actor)
    row = db.get(AdminPermission, grant_id)
    if row is None:
        raise NotFoundError("مجوز یافت نشد")
    now = datetime.now(UTC)
    if row.revoked_at is None:
        row.revoked_at = now
        row.revoked_by = actor.id
        audit(
            db,
            actor.id,
            "permission_revoke",
            "user",
            row.user_id,
            {"grant_id": row.id, "permission": row.permission},
            commit=False,
        )
    db.commit()
    return {"status": "revoked", "grant_id": grant_id}

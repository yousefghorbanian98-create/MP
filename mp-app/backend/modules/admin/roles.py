"""مدیریت «admin pass» = اعطا/ابطال نقش (M43-c1) — فقط مالک سیستم (super_admin).

قاعده‌های ایمنی:
- تغییر نقش خودِ فرد ممنوع (جلوی قفل‌شدن/تنزل خودخواسته)
- هر تغییر ← AuditLog (غیرقابل‌حذف)
- نقش نامعتبر رد می‌شود (fail loud)
"""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, ForbiddenError, NotFoundError
from db.models import AuditLog, User

ASSIGNABLE_ROLES = ("member", "reception", "coach", "manager", "admin", "super_admin")


def list_users(db: Session, *, limit: int = 100) -> list[dict]:
    rows = db.scalars(select(User).order_by(User.id).limit(limit)).all()
    return [
        {
            "id": u.id,
            "phone": u.phone,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": bool(u.is_active),
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }
        for u in rows
    ]


def set_role(db: Session, *, actor: User, user_id: int, role: str) -> dict:
    """اعطا/تغییر نقش (admin pass). actor باید super_admin باشد."""
    if actor.role != "super_admin":
        raise ForbiddenError("فقط مالک سیستم (super_admin) می‌تواند نقش بدهد")
    if actor.id == user_id:
        raise ApiError("تغییر نقش خودتان مجاز نیست — قفل‌شدن احتمالی", code="self_role_change")
    if role not in ASSIGNABLE_ROLES:
        raise ApiError(f"نقش «{role}» معتبر نیست", code="invalid_role")
    target = db.get(User, user_id)
    if target is None:
        raise NotFoundError("کاربر یافت نشد")
    old_role = target.role
    if old_role == role:
        return {"id": target.id, "role": role, "changed": False, "reason": "همان نقش فعلی است"}
    target.role = role
    db.add(
        AuditLog(
            actor_user_id=actor.id,
            action="role_grant",
            entity_type="user",
            entity_id=target.id,
            detail=json.dumps({"old_role": old_role, "new_role": role}, ensure_ascii=False),
        )
    )
    db.commit()
    return {
        "id": target.id,
        "role": role,
        "changed": True,
        "reason": f"نقش از {old_role} به {role} تغییر کرد (admin pass) — ثبت در لاگ ممیزی",
    }


def revoke_role(db: Session, *, actor: User, user_id: int) -> dict:
    """ابطال admin pass ← بازگشت به member."""
    return set_role(db, actor=actor, user_id=user_id, role="member")

"""روتر admin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.deps import CurrentUser, DbSession, require_permission
from app.errors import ForbiddenError
from modules.admin import service
from modules.admin.schemas import AuditOut, FeatureFlagIn, FeatureFlagOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_permission())])


@router.get("/audit", response_model=list[AuditOut], summary="لاگ ممیزی (US-406)")
def list_audit(db: DbSession, action: str | None = Query(None), limit: int = Query(100, le=500)):
    return service.list_audit(db, action=action, limit=limit)


@router.get("/flags/{key}", response_model=FeatureFlagOut, summary="وضعیت flag")
def get_flag(key: str, db: DbSession):
    return service.get_flag(db, key)


@router.put("/flags", response_model=FeatureFlagOut, summary="تنظیم feature flag (US-405)")
def set_flag(payload: FeatureFlagIn, db: DbSession):
    return service.set_flag(db, payload.key, payload.enabled, payload.description)


from modules.admin.kpis import admin_kpis as _admin_kpis  # noqa: E402


@router.get("/analytics/leaderboards", summary="لیدربوردهای مدیریتی: بهترین ورزشکار/بیشترین هزینه/بیشترین مراجعه (M42-c1)")
def _leaderboards(
    db: DbSession,
    limit: int = Query(10, ge=1, le=50),
    window_days: int = Query(30, ge=1, le=365),
):
    from modules.admin.analytics import leaderboards

    return leaderboards(db, limit=limit, window_days=window_days)


@router.get("/kpis", summary="KPI های واقعی داشبورد (M29)")
def _kpis(db: DbSession):
    return _admin_kpis(db)


# ── M43: admin pass — اعطا/ابطال نقش [finn] ──


class RoleIn(BaseModel):
    role: str = Field(..., min_length=2, max_length=20)


@router.get("/users", summary="فهرست کاربران و نقش‌ها (M43-c1)")
def users_list(db: DbSession, user: CurrentUser):
    if user.role != "super_admin":
        raise ForbiddenError("فقط مالک سیستم (super_admin)")
    from modules.admin.roles import list_users

    return list_users(db)


@router.post("/users/{user_id}/role", summary="اعطا/تغییر نقش = admin pass (M43-c1)")
def grant_role(user_id: int, payload: RoleIn, db: DbSession, user: CurrentUser):
    from modules.admin.roles import set_role

    return set_role(db, actor=user, user_id=user_id, role=payload.role)


@router.delete("/users/{user_id}/role", summary="ابطال admin pass ← بازگشت به member (M43-c1)")
def revoke_role(user_id: int, db: DbSession, user: CurrentUser):
    from modules.admin.roles import revoke_role as _revoke

    return _revoke(db, actor=user, user_id=user_id)

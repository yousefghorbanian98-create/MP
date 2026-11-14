"""روتر admin."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import DbSession, require_permission
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


@router.get("/kpis", summary="KPI های واقعی داشبورد (M29)")
def _kpis(db: DbSession):
    return _admin_kpis(db)

"""روتر آپدیت تفاضلی — عمومی (بدون auth؛ بررسی نسخه پیش از ورود)."""

from __future__ import annotations

from fastapi import APIRouter, Query

from modules.updates import service

router = APIRouter(prefix="/updates", tags=["updates"])


@router.get("/manifest", summary="مانیفست آپدیت تفاضلی (M20)")
def manifest(
    platform: str = Query(..., pattern="^(android|web|kiosk)$"),
    current: str = Query("0.0.0", max_length=20),
):
    return service.build_manifest(platform, current)

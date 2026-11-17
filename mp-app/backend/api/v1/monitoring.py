"""روتر مانیتورینگ — /metrics + /health/ready."""

from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST

from app.metrics import metrics

router = APIRouter(tags=["health"])


@router.get("/metrics", summary="متریک‌های Prometheus-style")
def prometheus_metrics() -> Response:
    return Response(content=metrics.render(), media_type=CONTENT_TYPE_LATEST)


@router.get("/health/ready", summary="آمادگی سرویس (readiness)")
def ready() -> Response:
    from sqlalchemy import text

    from db.base import get_engine
    from modules.auth.router import rate_limit_storage_healthy

    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False

    rate_limit_storage_ok = rate_limit_storage_healthy()
    ready_ok = db_ok and rate_limit_storage_ok
    return JSONResponse(
        status_code=200 if ready_ok else 503,
        content={
            "ready": ready_ok,
            "database_ok": db_ok,
            "rate_limit_storage_ok": rate_limit_storage_ok,
            "checkin_slo_ok": metrics.checkin_slo_ok(),
        },
    )

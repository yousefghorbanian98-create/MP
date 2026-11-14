"""روتر مانیتورینگ — /metrics + /health/ready."""

from __future__ import annotations

from fastapi import APIRouter, Response

from app.metrics import metrics

router = APIRouter(tags=["health"])


@router.get("/metrics", summary="متریک‌های Prometheus-style")
def prometheus_metrics() -> Response:
    return Response(content=metrics.render(), media_type="text/plain; version=0.0.4")


@router.get("/health/ready", summary="آمادگی سرویس (readiness)")
def ready() -> dict:
    from db.base import get_engine

    try:
        with get_engine().connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_ok = True
    except Exception:  # noqa: BLE001
        db_ok = False
    slo_ok = metrics.checkin_slo_ok()
    return {"ready": db_ok, "checkin_slo_ok": slo_ok}

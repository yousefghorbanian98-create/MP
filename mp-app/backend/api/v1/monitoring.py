"""روتر مانیتورینگ — /metrics + /health/ready."""

from __future__ import annotations

from fastapi import APIRouter, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST

from app.metrics import metrics

router = APIRouter(tags=["health"])


@router.get("/metrics", summary="متریک‌های Prometheus-style")
def prometheus_metrics() -> Response:
    # QF-27: عمق صف از DB خوانده می‌شود؛ اگر DB در دسترس نبود، متریک قبلی
    # نمایش داده می‌شود — `/metrics` نباید به‌خاطر دیتابیس ۵۰۰ بدهد.
    try:
        from db.base import get_session_factory
        from modules.outbox.health import refresh_metrics

        with get_session_factory()() as db:
            refresh_metrics(db)
    except Exception:  # noqa: BLE001 - scrape نباید بشکند
        pass
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
    payload: dict = {
        "database_ok": db_ok,
        "rate_limit_storage_ok": rate_limit_storage_ok,
        "checkin_slo_ok": metrics.checkin_slo_ok(),
    }

    # QF-27: صف outbox و heartbeat worker — فقط وقتی DB سالم است معنا دارد.
    worker_ok = True
    if db_ok:
        try:
            from app.config import settings
            from db.base import get_session_factory
            from modules.outbox.health import queue_stats, worker_status

            with get_session_factory()() as db:
                payload["outbox"] = queue_stats(db)
                status = worker_status(db)
            if settings.require_worker:
                worker_ok = bool(status["ok"])
                payload["worker_ok"] = worker_ok
                payload["worker"] = status
        except Exception:  # noqa: BLE001 - readiness نباید به‌خاطر یک جدول بشکند
            payload["outbox"] = {"error": "unavailable"}

    ready_ok = db_ok and rate_limit_storage_ok and worker_ok
    return JSONResponse(
        status_code=200 if ready_ok else 503,
        content={"ready": ready_ok, **payload},
    )

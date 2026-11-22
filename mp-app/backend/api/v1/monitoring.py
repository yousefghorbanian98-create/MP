"""روتر مانیتورینگ — /metrics + /health/ready."""

from __future__ import annotations

import hmac
import logging
import threading

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST

from app.config import settings
from app.errors import ForbiddenError, UnauthorizedError
from app.metrics import metrics

_scrape_errors_lock = threading.Lock()
_scrape_errors = 0


def _log_scrape_failure() -> None:
    """WP 2.5 / F‑17: خطای scrape ⇒ `logger.warning` با traceback + شمارنده.

    شمارنده هم در `/metrics` (برای هشدار) و هم در `/health/ready` (برای عیب‌یابی سریع) دیده می‌شود.
    """
    global _scrape_errors
    logging.getLogger(__name__).warning("refresh_metrics failed", exc_info=True)
    metrics.inc("mp_metrics_scrape_errors_total")
    with _scrape_errors_lock:
        _scrape_errors += 1


def scrape_error_count() -> int:
    with _scrape_errors_lock:
        return _scrape_errors


router = APIRouter(tags=["health"])


def require_metrics_token(request: Request) -> None:
    """گارد `/metrics` (WP 1.3 / F-06): Bearer با `MP_METRICS_TOKEN`.

    - توکن تنظیم‌نشده ⇒ ۴۰۳ (endpoint بسته است).
    - هدر نبود یا توکن غلط ⇒ ۴۰۱.
    مقایسهٔ ثابت‌زمان (`hmac.compare_digest`) برای جلوگیری از timing leak.
    """
    expected = settings.metrics_token
    if not expected:
        raise ForbiddenError("متریک‌ها در این محیط غیرفعال‌اند", code="metrics_disabled")
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not hmac.compare_digest(
        token.strip().encode(), expected.encode()
    ):
        raise UnauthorizedError("توکن متریک معتبر نیست")


require_metrics_token.__rbac__ = "metrics_token"  # type: ignore[attr-defined]


@router.get(
    "/metrics",
    summary="متریک‌های Prometheus-style (نیازمند Bearer)",
    dependencies=[Depends(require_metrics_token)],
)
def prometheus_metrics() -> Response:
    # QF-27: عمق صف از DB خوانده می‌شود؛ اگر DB در دسترس نبود، متریک قبلی
    # نمایش داده می‌شود — `/metrics` نباید به‌خاطر دیتابیس ۵۰۰ بدهد.
    try:
        from db.base import get_session_factory
        from modules.outbox.health import refresh_metrics

        with get_session_factory()() as db:
            refresh_metrics(db)
    except Exception:  # noqa: BLE001 - scrape نباید بشکند
        # WP 4.5 (S110): خطای به‌روزرسانی متریک بی‌صدا رد نمی‌شود؛ ثبت در سطح debug.
        _log_scrape_failure()
    try:
        from app.pool_metrics import publish_pool_gauges
        from db.base import get_engine

        publish_pool_gauges(get_engine(), metrics)
    except Exception:  # noqa: BLE001 - scrape نباید بشکند (WP 2.2)
        _log_scrape_failure()
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
    # WP 2.2 / F‑04: اشباع پایدار استخر ⇒ readiness قرمز (D‑13 C8)
    from app.pool_metrics import pool_saturated

    pool_sat = pool_saturated(get_engine())
    payload: dict = {
        "db_pool_saturated": pool_sat,
        "database_ok": db_ok,
        "rate_limit_storage_ok": rate_limit_storage_ok,
        "checkin_slo_ok": metrics.checkin_slo_ok(),
        # WP 2.5 / F‑17: بازتاب شمارندهٔ خطای scrape (کیت: «بازتاب در /health/ready»).
        "metrics_scrape_errors": scrape_error_count(),
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

    ready_ok = db_ok and rate_limit_storage_ok and worker_ok and not pool_sat
    return JSONResponse(
        status_code=200 if ready_ok else 503,
        content={"ready": ready_ok, **payload},
    )

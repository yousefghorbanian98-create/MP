"""ساختار اصلی FastAPI — app factory + OpenAPI + exception handlers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.errors import ApiError, api_error_handler, http_error_handler, validation_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init_db فقط برای dev — production با alembic migration می‌سازد
    _log_effective_configuration()
    if settings.environment == "development":
        from db.base import init_db

        init_db()
    yield


def _rate_limit_handler(request, exc):  # noqa: ARG001
    """پاسخ ۴۲۹ یکنواخت — handler ماژول‌سطح (رفع یافتهٔ semgrep useless-inner-function)."""
    from app.errors import _payload_for_rate_limit

    return JSONResponse(
        status_code=429,
        content=_payload_for_rate_limit(),
    )


def health() -> dict:
    """سلامت سیستم — endpoint سطح ماژول (رفع FP semgrep)."""
    return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}


def _assert_explicit_environment() -> None:
    """WP 1.2 / F-02: بدون MP_ENVIRONMENT صریح، اپ بالا نمی‌آید (fail-safe).

    پیش‌فرض کلاس `development` است؛ اگر استقرار متغیر را فراموش کند، قبلاً اپ با
    پیام‌رسان dev و نشت کد OTP بالا می‌آمد. تست‌های خودکار با
    `MP_ALLOW_IMPLICIT_DEV=true` (در tests/conftest.py) اجازه دارند.
    """
    if "environment" in settings.model_fields_set or settings.allow_implicit_dev:
        return
    raise RuntimeError(
        "MP_ENVIRONMENT باید صریح تنظیم شود (development یا production)؛ "
        "پیش‌فرض ضمنی برای بالا آمدن مجاز نیست"
    )


def _log_effective_configuration() -> None:
    """WP 1.2 / F-02: یک WARNING با محیط مؤثر و پیام‌رسان تا اشتباه دیده شود."""
    from app.logging import get_logger

    get_logger("startup").warning(
        "effective_configuration",
        environment=settings.environment,
        sms_provider=settings.sms_provider,
        dev_otp_echo=bool(settings.environment == "development" and settings.allow_dev_otp_echo),
        rate_limit_storage="valkey" if settings.environment == "production" else "memory",
        log_format="json" if settings.environment != "development" else "console",
        init_db_on_startup=settings.environment == "development",
        trusted_proxies_configured=bool(settings.trusted_proxies.strip()),
    )


def create_app() -> FastAPI:
    _assert_explicit_environment()
    # M46-c3 — لاگ ساختاریافته را واقعاً روشن کن.
    # پیش از این `configure_logging` تعریف شده بود ولی هیچ‌جا صدا زده نمی‌شد،
    # پس `get_logger("jobs")` در scheduler به پیکربندی پیش‌فرض structlog می‌افتاد.
    from app.logging import configure_logging

    configure_logging(json_logs=settings.environment != "development")

    app = FastAPI(
        title="Muscle Paradise API",
        description=(
            "سیستم‌عامل باشگاه Muscle Paradise — قرارداد REST نسخه‌دار. "
            "قاعدهٔ G8: اعداد بار/ست/تکرار فقط از موتور قواعد می‌آیند."
        ),
        version="1.0.0",
        openapi_tags=[
            {"name": "health", "description": "سلامت سیستم"},
            {"name": "auth", "description": "احراز هویت OTP و نشست"},
            {"name": "members", "description": "اعضا و اشتراک‌ها"},
            {"name": "payments", "description": "پرداخت و کیف‌پول"},
            {"name": "assessment", "description": "ارزیابی ۱۴ دامنه و JP7"},
            {"name": "programs", "description": "برنامهٔ تمرین (تأیید مربی)"},
            {"name": "nutrition", "description": "برنامهٔ تغذیه"},
            {"name": "face-id", "description": "چهره و چک‌این"},
            {"name": "notifications", "description": "اعلان‌ها"},
            {"name": "admin", "description": "مدیریت، audit، feature flags"},
        ],
        lifespan=lifespan,
    )

    # CORS: allowlist محیطی (D-22c2 — حذف wildcard). production خالی = fail-closed.
    _origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.security.headers import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware, production=settings.environment == "production")

    from app.metrics import metrics

    @app.middleware("http")
    async def record_http_metrics(request, call_next):
        started_at = perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            route_name = getattr(route, "path", "unmatched")
            metrics.inc(
                "mp_http_requests_total",
                method=request.method,
                route=route_name,
                status=str(status_code),
            )
            metrics.observe(
                "mp_http_request_duration_seconds",
                perf_counter() - started_at,
                method=request.method,
                route=route_name,
            )

    # OSS middleware validates or generates a bounded X-Request-ID and returns
    # it in the response. It is outermost so request IDs exist on error paths too.
    from asgi_correlation_id import CorrelationIdMiddleware

    app.add_middleware(CorrelationIdMiddleware, header_name="X-Request-ID")

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    from modules.auth.router import limiter

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    # M60/R18 — کفِ کیفیت خطا: هیچ درخواستی ۵۰۰ خالی نمی‌گیرد. جای این هندلر
    # آخر است تا بالاتر از ApiError/Validation قرار بگیرد و فقط خطاهای
    # *غیرمنتظره* را بگیرد (یافتهٔ DAST: OverflowError/IntegrityError).
    from app.unhandled import register as register_unhandled

    register_unhandled(app)

    # M60/R18 — سقف شناسه‌های عددی در مسیر، قبل از رسیدن به DB
    # (بدون این، `GET /shop/products/10**30` ← OverflowError ← ۵۰۰).
    from app.id_guard import register as register_id_guard

    register_id_guard(app)

    # تصاویر کتابخانهٔ حرکات (G9) — از خود اپ سرو می‌شوند تا PWA آفلاین
    # هم تصویر داشته باشد؛ هیچ وابستگی به سرور بیرونی نیست.
    from fastapi.staticfiles import StaticFiles

    from api.v1.api import api_router

    _static = Path(__file__).resolve().parents[1] / "static"
    if _static.is_dir():
        app.mount("/static", StaticFiles(directory=_static), name="static")

    app.include_router(api_router, prefix="/api/v1")
    app.add_api_route("/health", health, methods=["GET"], tags=["health"], summary="سلامت سیستم")

    return app


app = create_app()

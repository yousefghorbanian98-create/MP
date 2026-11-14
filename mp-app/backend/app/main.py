"""ساختار اصلی FastAPI — app factory + OpenAPI + exception handlers."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.errors import ApiError, api_error_handler, validation_error_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # init_db فقط برای dev — production با alembic migration می‌سازد
    if settings.environment == "development":
        from db.base import init_db

        init_db()
    yield


def create_app() -> FastAPI:
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.security.headers import SecurityHeadersMiddleware

    app.add_middleware(SecurityHeadersMiddleware, production=settings.environment == "production")

    app.add_exception_handler(ApiError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    from app.errors import _payload_for_rate_limit
    from modules.auth.router import limiter

    app.state.limiter = limiter

    def _rate_limit_handler(request, exc):  # noqa: ANN001
        return JSONResponse(
            status_code=429,
            content=_payload_for_rate_limit(),
        )

    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    from api.v1.api import api_router

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health", tags=["health"], summary="سلامت سیستم")
    def health() -> dict:
        return {"status": "ok", "service": settings.app_name, "version": "1.0.0"}

    return app


app = create_app()

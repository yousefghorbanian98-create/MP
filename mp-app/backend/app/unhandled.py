"""M60/R18 — هندلرِ خطای غیرمنتظره: هیچ درخواستی نباید بی‌پاسخ بماند.

# یافتهٔ واقعی (DAST جانشین)

`scripts/dast.py` (schemathesis روی OpenAPI خودِ اپ) روی چند مسیر کرش پیدا کرد:

    GET    /api/v1/members                    → OverflowError
    PATCH  /api/v1/members/{member_id}        → OverflowError
    GET    /api/v1/assessments/limb/…/report  → OverflowError
    POST   /api/v1/programs/set-feedback      → IntegrityError
    POST   /api/v1/nutrition/weight-logs      → IntegrityError
    POST   /api/v1/ai/program/generate        → IntegrityError

در تولید (`TestClient(raise_server_exceptions=False)`، همان‌طور که uvicorn
کار می‌کند) این‌ها یک چیز را برمی‌گرداندند: **۵۰۰ خالی بدون بدنه**. کلاینت
فلاتر `_decode` را روی بدنهٔ خالی اجرا می‌کرد و پیام «خطای سرور (۵۰۰)» را
نشان می‌داد؛ اپراتور هم هیچ سرنخی از *کدام* درخواست داشت.

این ماژول سه چیز را تضمین می‌کند:

۱. پاسخ همیشه همان قالب خطای پروژه است: `{"error": {"code", "message"}}`.
۲. جزئیات فنی (نوع خطا + مسیر) در لاگ می‌رود، نه در پاسخ (نشت اطلاعات نداریم).
۳. شمارندهٔ متریک `mp_unhandled_errors_total{path,type}` بالا می‌رود، پس
   ۵۰۰ها در `/metrics` دیده می‌شوند و می‌شود هشدار گذاشت.

# چرا هندلر و نه «رفع تک‌تک»

رفع تک‌تک مسیرها باگ‌ها را کم می‌کند ولی کلاسِ مشکل را باقی می‌گذارد: هر
endpoint آینده که یک ورودی عجیب را درست اعتبارسنجی نکند، دوباره ۵۰۰ خالی
می‌دهد. هندلر کف کیفیت را تضمین می‌کند؛ رفع ریشه‌ای (اعتبارسنجی ورودی) هنوز
لازم است و در گزارش به‌عنوان بدهی باز ثبت شده.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError

from app.logging import get_logger

logger = get_logger("mp.errors")

# متن ثابت — هیچ‌وقت str(exc) در پاسخ نمی‌آید (نشت مسیر فایل/SQL/جزئیات DB).
UNEXPECTED_MESSAGE = "خطای غیرمنتظرهٔ سرور. رخداد ثبت شد."


REFERENCE_MESSAGE = "شناسهٔ ارجاع‌شده وجود ندارد یا با دادهٔ فعلی نمی‌خواند."
CONFLICT_MESSAGE = "این داده با وضعیت فعلی تعارض دارد."
POOL_EXHAUSTED_MESSAGE = "ظرفیت اتصال پایگاه داده موقتاً پر است؛ چند لحظه بعد دوباره تلاش کنید."


def _integrity_payload(exc: IntegrityError) -> tuple[int, dict]:
    """`IntegrityError` ← ۴xx، نه ۵۰۰.

    دو حالت واقعی که DAST با idهای تصادفی ساخت:
      • FOREIGN KEY  ← شناسهٔ ارجاع‌شده (member_id/coach_id/program_id) وجود ندارد
      • UNIQUE/CHECK ← رکورد تکراری یا نقض قید

    هر دو خطای **کاربر** هستند، نه خطای سرور. پیش از این ۵۰۰ می‌گرفتند
    (`POST /programs/set-feedback`, `/nutrition/weight-logs`, `/classes`, …)
    و اپراتور فکر می‌کرد سرویس خراب است.
    """
    raw = str(getattr(exc, "orig", exc)).lower()
    if "foreign key" in raw:
        return 422, {"error": {"code": "invalid_reference", "message": REFERENCE_MESSAGE}}
    return 409, {"error": {"code": "conflict", "message": CONFLICT_MESSAGE}}


def register(app: FastAPI) -> None:
    @app.exception_handler(IntegrityError)
    async def _integrity(request: Request, exc: IntegrityError) -> JSONResponse:
        status_code, content = _integrity_payload(exc)
        logger.warning(
            "integrity_violation",
            method=request.method,
            path=request.url.path,
            status_code=status_code,
        )
        return JSONResponse(status_code=status_code, content=content)

    @app.exception_handler(PoolTimeoutError)
    async def _pool_timeout(request: Request, exc: PoolTimeoutError) -> JSONResponse:
        # WP 2.2 / F‑04 (D‑13 C7): پر بودن استخر ⇒ ۵۰۳ + Retry-After، نه ۵۰۰.
        from app.metrics import metrics

        metrics.inc("mp_db_pool_timeout_total")
        logger.warning(
            "db_pool_exhausted",
            method=request.method,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": "1"},
            content={"error": {"code": "db_pool_exhausted", "message": POOL_EXHAUSTED_MESSAGE}},
        )

    @app.exception_handler(Exception)
    async def _unexpected(request: Request, exc: Exception) -> JSONResponse:
        from app.metrics import metrics

        # برچسب متریک باید کارتینالیتی پایین داشته باشد. `scope["route"].path`
        # در FastAPI 0.163 فقط بخشِ نسبیِ روتر را می‌دهد (`/members` بدون
        # `/api/v1`)؛ پس از مسیر واقعی استفاده می‌کنیم و هر بخشِ عددی را با
        # `{id}` جایگزین می‌کنیم — نه ۵۰۰ برچسب مختلف برای ۵۰۰ شناسه.
        template = "/".join("{id}" if seg.isdigit() else seg for seg in request.url.path.split("/"))
        metrics.inc("mp_unhandled_errors_total", path=template, type=type(exc).__name__)
        logger.exception(
            "unhandled_error",
            method=request.method,
            path=request.url.path,
            error_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": UNEXPECTED_MESSAGE}},
        )

"""قالب خطای یکپارچهٔ API — همهٔ خطاها با ساختار ثابت."""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    """خطای ساختاریافتهٔ API."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        code: str = "bad_request",
        details: list | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or []


class NotFoundError(ApiError):
    def __init__(self, message: str = "منبع یافت نشد"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "not_found")


class ForbiddenError(ApiError):
    def __init__(self, message: str = "دسترسی غیرمجاز", code: str | None = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, code or "forbidden")


class UnauthorizedError(ApiError):
    def __init__(self, message: str = "احراز هویت لازم است"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "unauthorized")


class ConflictError(ApiError):
    def __init__(self, message: str = "تداخل", code: str = "conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT, code)


def _payload(code: str, message: str, details: list | None = None) -> dict:
    return {"error": {"code": code, "message": message, "details": details or []}}


def _payload_for_rate_limit() -> dict:
    return _payload("rate_limited", "تعداد درخواست‌ها زیاد است؛ کمی بعد تلاش کنید")


async def api_error_handler(request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_payload(exc.code, exc.message, exc.details),
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = [
        {
            "loc": [str(x) for x in e.get("loc", [])],
            "msg": e.get("msg", ""),
            "type": e.get("type", ""),
        }
        for e in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_payload("validation_error", "داده‌های ورودی معتبر نیستند", details),
    )

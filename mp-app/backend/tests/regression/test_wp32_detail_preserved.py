"""WP 3.2 regression — پیام خاص HTTPExceptionهای برنامه نباید در پاکت یکدست حذف شود.

قبل از اصلاح: `HTTPException(404, detail="authority نامعتبر")` ⇒ پیام عمومی «منبع یافت نشد» (اطلاعات گم می‌شد).
"""

from __future__ import annotations

import asyncio
import json

from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import http_error_handler


def _render(exc: StarletteHTTPException) -> dict:
    resp = asyncio.run(http_error_handler(None, exc))  # type: ignore[arg-type]
    return {"status": resp.status_code, "body": json.loads(resp.body)}


def test_app_detail_message_is_kept_for_404() -> None:
    out = _render(StarletteHTTPException(status_code=404, detail="authority نامعتبر"))
    assert out["status"] == 404
    assert out["body"]["error"]["message"] == "authority نامعتبر"


def test_starlette_default_404_still_gets_project_message() -> None:
    out = _render(StarletteHTTPException(status_code=404, detail="Not Found"))
    assert out["body"]["error"]["message"] == "منبع یافت نشد"
    assert out["body"]["error"]["code"] == "not_found"


def test_starlette_default_405_still_gets_project_message() -> None:
    out = _render(StarletteHTTPException(status_code=405, detail="Method Not Allowed"))
    assert out["body"]["error"]["code"] == "method_not_allowed"

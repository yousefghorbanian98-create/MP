"""WP 3.1 / F‑25 — کف و سقف شناسهٔ مسیر پس از مسیریابی.

`id_guard` (middleware) فقط بخش‌های عددیِ خامِ URL را از سقف عبور می‌دهد و مقادیر منفی و `0` را نمی‌بیند
(`"-1".isdigit()` نادرست است). این dependency سراسری، **بعد از مسیریابی** و فقط روی پارامترهای
`*_id` (در OpenAPI همه integer)، مقدار را با الگوی صریح `^[+-]?\\d+$` می‌سنجد؛ رشته‌ها دست‌نخورده می‌مانند.

قاعده: `v < 1` یا `v > MAX_SAFE_ID` ⇒ ۴۲۲ با `error.code = "invalid_id"`.
نکته: `lstrip("+-")` روی رشتهٔ اصلی به کار نمی‌رود (`"-1"` را `1` می‌کرد).
"""

from __future__ import annotations

import re

from fastapi import Request, status

from app.deps import MAX_SAFE_ID
from app.errors import ApiError

_INT_RE = re.compile(r"[+-]?[0-9]+\Z", re.ASCII)
_MSG = "شناسهٔ مسیر خارج از بازهٔ مجاز است."


async def check_path_id_floor(request: Request) -> None:
    for name, raw in request.path_params.items():
        if not name.endswith("_id") or not isinstance(raw, str):
            continue
        if not _INT_RE.match(raw):
            continue  # غیرعددی: اعتبارسنجی نوع FastAPI تصمیم می‌گیرد
        value = int(raw)  # پس از تطبیق با regex؛ بدون lstrip
        if value < 1 or value > MAX_SAFE_ID:
            raise ApiError(
                _MSG, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, code="invalid_id"
            )

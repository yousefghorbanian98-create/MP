"""M60/R18 — سقفِ شناسه‌های مسیر، به‌صورت یک middleware (نه ۴۱ امضای تابع).

# یافتهٔ DAST

`int` خالی در امضای endpoint هر عدد صحیحی را می‌پذیرد — از جمله `10**30`.
SQLite (و ستون INTEGER هر DB دیگری) چنین مقداری را نمی‌پذیرد و
`OverflowError` می‌دهد. نتیجه در تولید: ۵۰۰ روی مسیرهای ساده‌ای مثل

    GET  /api/v1/shop/products/999999999999999999999999999999
    GET  /api/v1/notifications/reminders/member/10**30
    POST /api/v1/shop/cart           (with product_id: 10**30)
    POST /api/v1/assessments         (member_id: 10**30)

# چرا middleware و نه `PathId` در هر امضا

`PathId` راه درست در سطح تایپ است، اما نیاز به تغییر ۴۱ امضا دارد و هر
endpoint جدیدی که فراموش کند دوباره سوراخ می‌شود. این middleware همان قاعده
را **یک‌جا** اعمال می‌کند: هر بخشِ کاملاً عددی از مسیر که از `2**53` بزرگ‌تر
باشد (یا طولش > ۱۹ رقم) همان ۴۲۲ قالب‌پروژه را می‌گیرد، پیش از آنکه به
لایهٔ داده برسد.

`2**53` انتخاب شد چون:
  • `Number.MAX_SAFE_INTEGER` در جاوااسکریپت (استودیو) و کلاینت فلاتر
  • سقف `MAX_SAFE_ID` در `app/deps.py` — دو لایه هم‌خوان، نه دو عدد متفاوت

اعداد بزرگ‌تر از این هیچ معنای دامنه‌ای ندارند: شناسهٔ رکورد در sqlite
حداکثر ۶۴بیتی است و BIGINT امضاشده تا ۹.۲e۱۸ می‌رود؛ ۹e۱۵ هم بسیار بیش از
ظرفیت واقعی باشگاه است.

بدنهٔ JSON (`{"member_id": 10**30}`) هم همین کلاس خطا را دارد؛ آن با
اعتبارسنجی `PathId`-مانند در اسکیمای pydantic حل می‌شود و در گزارش به‌عنوان
بدهی باقی‌مانده ثبت شده (تست DAST آن را ۵۰۰ نشان می‌دهد، شکل پاسخ درست است).
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

MAX_SAFE_ID = 9_007_199_254_740_991
MAX_ID_LEN = len(str(MAX_SAFE_ID))  # ۱۶

BODY = {
    "error": {
        "code": "invalid_id",
        "message": "شناسهٔ مسیر خارج از بازهٔ مجاز است.",
    }
}


def _too_big(segment: str) -> bool:
    if not segment.isdigit() or not segment.isascii():
        return False
    if len(segment) > MAX_ID_LEN + 3:  # صفرهای ابتدایی را هم می‌گیرد
        return True
    return len(segment) > MAX_ID_LEN or int(segment) > MAX_SAFE_ID


def register(app: FastAPI) -> None:
    @app.middleware("http")
    async def _id_ceiling(request: Request, call_next):
        if any(_too_big(seg) for seg in request.url.path.split("/")):
            return JSONResponse(status_code=422, content=BODY)
        return await call_next(request)

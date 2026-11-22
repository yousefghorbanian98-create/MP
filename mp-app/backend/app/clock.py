"""«امروز» یکتا برای دامنهٔ سلامت و تغذیه (WP 3.6، F‑28، AD‑1).

منطقهٔ مرجع `settings.shop_timezone` است (پیش‌فرض Asia/Tehran). استفاده از
تابع today() کلاس date به ساعت کانتینر (UTC) وابسته است و هر شب ۰۰:۰۰–۰۳:۳۰ تهران روز
اشتباه می‌دهد؛ همهٔ این مسیرها باید از همین تابع بگیرند.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from app.config import settings


def _now_utc() -> datetime:
    """تنها نقطهٔ خواندن ساعت؛ در تست‌ها جایگزین می‌شود."""
    return datetime.now(UTC)


def today_in_shop_zone() -> date:
    """تاریخ امروز در منطقهٔ زمانی فروشگاه/تغذیه."""
    return _now_utc().astimezone(ZoneInfo(settings.shop_timezone)).date()

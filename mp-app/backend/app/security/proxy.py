"""IP واقعی کلاینت پشت پروکسی معتمد (QF-26).

# مسئله

`X-Forwarded-For` یک هدر است؛ هر کلاینتی می‌تواند آن را بفرستد. اگر بی‌قید
خوانده شود: لاگ و ممیزی IP جعلی نشان می‌دهد و محدودیت نرخ با تغییر هدر دور
زده می‌شود. اگر هرگز خوانده نشود: پشت nginx همهٔ درخواست‌ها IP پروکسی
می‌گیرند و محدودیت نرخ کل باشگاه را یک کاربر حساب می‌کند.

# قاعده

1. آدرس واقعی = `request.client.host`.
2. اگر آن آدرس در فهرست معتمد (`MP_TRUSTED_PROXIES`) بود، زنجیرهٔ XFF از
   **راست به چپ** پیموده می‌شود: هر hop معتمد رد می‌شود و اولین hop غیرمعتمد
   «کلاینت» است — همان قاعده‌ای که nginx/Cloudflare استفاده می‌کنند.
3. هر hop نامعتبر یا زنجیرهٔ خالی ⇒ برگشت به peer (fail-closed).

این ماژول فقط محاسبه می‌کند؛ تصمیم «چه کسی معتمد است» پیکربندی است.
"""

from __future__ import annotations

from ipaddress import ip_address

from starlette.requests import Request


def parse_trusted(raw: str | None) -> frozenset[str]:
    """فهرست جداشده با ویرگول → مجموعهٔ IP؛ ورودی خالی/فاصله‌ها نادیده."""
    if not raw:
        return frozenset()
    return frozenset(part.strip() for part in raw.split(",") if part.strip())


def _valid_ip(value: str) -> str | None:
    try:
        return str(ip_address(value.strip()))
    except ValueError:
        return None


def client_ip(request: Request, trusted: frozenset[str]) -> str:
    peer = request.client.host if request.client else ""
    if not trusted or peer not in trusted:
        return peer

    forwarded = request.headers.get("x-forwarded-for", "")
    hops = [hop for hop in (item.strip() for item in forwarded.split(",")) if hop]
    if not hops:
        return peer

    for hop in reversed(hops):
        normalized = _valid_ip(hop)
        if normalized is None:
            # زنجیرهٔ نیمه‌معتبر: ادعای IP نامعتبر = برگشت به peer، نه اعتماد جزئی.
            return peer
        if normalized not in trusted:
            return normalized
    # همهٔ hopها معتمدند: آخرین (نزدیک‌ترین به ما) معتبرترین چیزی است که داریم.
    return _valid_ip(hops[0]) or peer


def rate_limit_key(request: Request, trusted: frozenset[str]) -> str:
    """کلید محدودیت نرخ؛ هدر جعلی بدون peer معتمد سهمیهٔ تازه نمی‌سازد."""
    return client_ip(request, trusted)

"""لایهٔ ارسال پیامک (M28) — الگوی Adapter با ارائه‌دهندگان ایرانی.

قابلیت دلتا/بدون حذف‌نصب: ارائه‌دهنده با تنظیم `sms_provider` تعویض می‌شود؛
حالت توسعه (`dev`) کد را در پاسخ API برمی‌گرداند (مثل قبل — سازگاری عقب‌رو).
"""

from __future__ import annotations

import logging
from typing import Protocol

from app.config import settings

log = logging.getLogger("mp.sms")


class SmsProvider(Protocol):
    name: str

    def send(self, phone: str, text: str) -> bool: ...


class DevSmsProvider:
    """توسعه — پیامک واقعی نمی‌فرستد؛ کد در پاسخ API برمی‌گردد."""

    name = "dev"

    def send(self, phone: str, text: str) -> bool:
        log.info("[SMS-DEV] %s ← %s", phone, text)
        return True


class WebMagfaProvider:
    """درگاه وب‌مغفا (ایران) — مستندات API: ارسال با GET/POST به sms_api_url."""

    name = "webmagfa"

    def send(self, phone: str, text: str) -> bool:
        import json
        import urllib.error
        import urllib.request

        payload = json.dumps(
            {
                "uname": settings.sms_username,
                "pass": settings.sms_password,
                "from": settings.sms_originator,
                "to": [phone],
                "text": text,
            }
        ).encode()
        req = urllib.request.Request(
            settings.sms_api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        if not settings.sms_api_url.startswith("https://"):
            log.error("[SMS] sms_api_url must be https")
            return False
        try:
            with (
                urllib.request.urlopen(  # nosec B310,nosemgrep — URL از تنظیمات اپراتور + اجبار https
                    req, timeout=10
                ) as resp
            ):
                return 200 <= resp.status < 300
        except (urllib.error.URLError, TimeoutError) as exc:
            log.error("[SMS-MAGFA] failed: %s", exc)
            return False


class KavenegarProvider:
    """کاوه‌نگار — پرکاربردترین درگاه ایرانی."""

    name = "kavenegar"

    def send(self, phone: str, text: str) -> bool:
        import urllib.error
        import urllib.parse
        import urllib.request

        url = f"{settings.sms_api_url.rstrip('/')}/{settings.sms_api_key}/send.json"
        data = urllib.parse.urlencode(
            {"receptor": phone, "message": text, "sender": settings.sms_originator}
        ).encode()
        if not settings.sms_api_url.startswith("https://"):
            log.error("[SMS] sms_api_url must be https")
            return False
        try:
            with (
                urllib.request.urlopen(  # nosec B310,nosemgrep — URL از تنظیمات اپراتور + اجبار https
                    url, data=data, timeout=10
                ) as resp
            ):
                return 200 <= resp.status < 300
        except (urllib.error.URLError, TimeoutError) as exc:
            log.error("[SMS-KAVENEGAR] failed: %s", exc)
            return False


_PROVIDERS: dict[str, type] = {
    "dev": DevSmsProvider,
    "webmagfa": WebMagfaProvider,
    "kavenegar": KavenegarProvider,
}


def get_sms_provider() -> SmsProvider:
    cls = _PROVIDERS.get(settings.sms_provider, DevSmsProvider)
    return cls()

"""لایهٔ ارسال پیامک (M28) — الگوی Adapter با ارائه‌دهندگان ایرانی.

قابلیت دلتا/بدون حذف‌نصب: ارائه‌دهنده با تنظیم `sms_provider` تعویض می‌شود؛
حالت توسعه (`dev`) کد را در پاسخ API برمی‌گرداند (مثل قبل — سازگاری عقب‌رو).
"""

from __future__ import annotations

import logging
from typing import Protocol

from app.config import settings

log = logging.getLogger("mp.sms")


def _log_provider_failure(message: str, *args: object, exc: BaseException) -> None:
    """ثبت خطای فراهم‌کننده با traceback بدون متن استثنا (F-29 + AD-6).

    `log.exception` متن استثنا را در traceback می‌گذارد، و متن `URLError`/`HTTPError`
    می‌تواند URL یا کلید API را داشته باشد (تست test_sms::credentials این نشت را گرفت).
    پس نوع استثنا و قاب‌های traceback ثبت می‌شوند، متن آن پنهان می‌شود.
    """
    redacted = RuntimeError("پیام استثنا پنهان شد (ممکن است کلید یا URL در آن باشد)")
    log.error(message, *args, exc_info=(type(exc), redacted, exc.__traceback__))


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
        req = urllib.request.Request(  # noqa: S310 — F-29: https در خط بعد اجبار می‌شود
            settings.sms_api_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        if not settings.sms_api_url.startswith("https://"):
            log.error("[SMS] sms_api_url must be https")
            return False
        try:
            with urllib.request.urlopen(  # nosec B310,nosemgrep  # noqa: S310 — F-29: URL از تنظیمات اپراتور + https اجباری
                req, timeout=10
            ) as resp:
                return 200 <= resp.status < 300
        except urllib.error.HTTPError as exc:
            _log_provider_failure("[SMS-MAGFA] provider returned HTTP %s", exc.code, exc=exc)
            return False
        except urllib.error.URLError as exc:
            _log_provider_failure(
                "[SMS-MAGFA] network request failed (%s)", type(exc.reason).__name__, exc=exc
            )
            return False
        except TimeoutError as exc:
            _log_provider_failure("[SMS-MAGFA] request timed out", exc=exc)
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
            with urllib.request.urlopen(  # nosec B310,nosemgrep  # noqa: S310 — F-29: URL از تنظیمات اپراتور + https اجباری
                url, data=data, timeout=10
            ) as resp:
                return 200 <= resp.status < 300
        except urllib.error.HTTPError as exc:
            _log_provider_failure("[SMS-KAVENEGAR] provider returned HTTP %s", exc.code, exc=exc)
            return False
        except urllib.error.URLError as exc:
            _log_provider_failure(
                "[SMS-KAVENEGAR] network request failed (%s)", type(exc.reason).__name__, exc=exc
            )
            return False
        except TimeoutError as exc:
            _log_provider_failure("[SMS-KAVENEGAR] request timed out", exc=exc)
            return False


_PROVIDERS: dict[str, type] = {
    "dev": DevSmsProvider,
    "webmagfa": WebMagfaProvider,
    "kavenegar": KavenegarProvider,
}


class SmsProviderConfigurationError(RuntimeError):
    """Provider selection must never silently downgrade to development SMS."""


def get_sms_provider() -> SmsProvider:
    cls = _PROVIDERS.get(settings.sms_provider)
    if cls is None:
        raise SmsProviderConfigurationError(
            f"SMS provider is not supported: {settings.sms_provider!r}"
        )
    if cls is DevSmsProvider and settings.environment == "production":
        raise SmsProviderConfigurationError(
            "The development SMS provider is disabled in production"
        )
    return cls()

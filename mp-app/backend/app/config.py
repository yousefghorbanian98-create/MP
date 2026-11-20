"""تنظیمات بک‌اند — از env / .env خوانده می‌شود (pydantic-settings)."""

from __future__ import annotations

import base64
import binascii
import ipaddress
from pathlib import Path
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# RFC 7518 §3.2 — HMAC-SHA256 با کلید کوتاه‌تر از ۳۲ بایت، امنیت اعلام‌شده را ندارد.
MIN_SECRET_BYTES = 32
DEFAULT_DEV_SECRET = "dev-secret-change-in-production-x"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="MP_", extra="ignore", hide_input_in_errors=True
    )

    app_name: str = "Muscle Paradise"
    environment: str = "development"
    database_url: str = "sqlite:///./mp.db"
    secret_key: str = DEFAULT_DEV_SECRET
    # نشانی بیرونیِ خودِ سرویس — بانکِ واقعی کاربر را به `callback` همین نشانی برمی‌
    # گرداند؛ در production باید MP_PUBLIC_BASE_URL=https://domain باشد.
    public_base_url: str = "http://127.0.0.1:8000"
    # manual = بدون درگاه اینترنتی (پیش‌فرض محصول). mock/sandbox فقط ابزار آزمون.
    payment_gateway: str = "manual"  # manual | mock | sandbox
    payment_sandbox: bool = True
    # M110 — بانک صندباکس محلی (devtools/sandbox_bank.py); هیچ اعتبار واقعی نمی‌خواهد
    sandbox_bank_url: str = "http://127.0.0.1:8088"
    sandbox_bank_merchant_id: str = "SANDBOX-MERCHANT"
    # کلید رمزنگاری FaceTemplate — در production حتماً از env تزریق می‌شود (base64, 32 bytes)
    biometric_key: str = ""
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    otp_ttl_seconds: int = 120
    # M28 — لایهٔ پیامک (app/sms.py): dev | webmagfa | kavenegar
    sms_provider: str = "dev"
    sms_api_url: str = ""
    sms_api_key: str = ""
    sms_username: str = ""
    sms_password: str = ""
    sms_originator: str = ""

    otp_max_attempts: int = 5
    otp_rate_limit: str = "10/minute"
    otp_burst_limit: str = "3/second"  # سقف انفجاری — ساعت اوج باشگاه (M22-c3)
    login_rate_limit: str = "10/minute"
    # M60 — فروشگاه. چرا اینجا و نه hardcode: مسیر خرید مسیر پول است؛
    # سقف باید قابل تنظیم باشد (پیک فروش/حراج) بدون تغییر کد.
    # QF-07 — فیش کارت‌به‌کارت: مسیر خصوصی، سقف حجم و TTL بازبینی.
    receipts_dir: str = "var/receipts"
    receipt_max_bytes: int = 5 * 1024 * 1024
    receipt_review_ttl_hours: int = 48
    shop_write_rate_limit: str = "30/minute"
    shop_checkout_rate_limit: str = "10/minute"
    # فاز ۲ (تصمیم مالک ۲۰۲۶-۱۱-۱۹): فروشگاه نمایش‌محور است. خرید درون‌برنامه‌ای
    # بسته است و خرید حضوری انجام می‌شود. این پرچم فقط برای تست موتور پول روشن
    # می‌شود؛ در production خاموش می‌ماند و مسیر سبد/تسویه ۴۰۹ می‌دهد.
    shop_online_purchase_enabled: bool = False
    # ساعت کاری باشگاه: منبع حقیقت پاسخ سرور است، نه ساعت دستگاه عضو.
    shop_timezone: str = "Asia/Tehran"
    shop_open_hour: int = 7
    shop_close_hour: int = 23
    # روزهای تعطیل هفتگی با کاما؛ ۰=دوشنبه … ۶=یکشنبه. خالی = بدون تعطیلی.
    shop_closed_weekdays: str = ""
    valkey_url: str = "redis://localhost:6379/0"
    # allowlist مبدأهای CORS — با کاما جدا شود (env: MP_CORS_ORIGINS)
    # در production باید صریح تنظیم شود؛ خالی = هیچ مبدأ مرورگری (fail-closed)
    cors_origins: str = (
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    )
    backend_dir: Path = Path(__file__).resolve().parent.parent

    @field_validator("sms_provider")
    @classmethod
    def _supported_sms_provider(cls, value: str) -> str:
        if value not in {"dev", "webmagfa", "kavenegar"}:
            raise ValueError("MP_SMS_PROVIDER باید dev، webmagfa یا kavenegar باشد")
        return value

    @field_validator("shop_timezone")
    @classmethod
    def _valid_timezone(cls, value: str) -> str:
        from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:  # pragma: no cover - تنظیم غلط
            raise ValueError(f"MP_SHOP_TIMEZONE نامعتبر است: {value}") from exc
        return value

    @field_validator("shop_open_hour", "shop_close_hour")
    @classmethod
    def _valid_hour(cls, value: int) -> int:
        if not 0 <= value <= 23:
            raise ValueError("ساعت کاری باید بین ۰ و ۲۳ باشد")
        return value

    @field_validator("shop_closed_weekdays")
    @classmethod
    def _valid_weekdays(cls, value: str) -> str:
        for chunk in value.split(","):
            text = chunk.strip()
            if not text:
                continue
            if not text.isdigit() or not 0 <= int(text) <= 6:
                raise ValueError("MP_SHOP_CLOSED_WEEKDAYS فقط عدد ۰ تا ۶ می‌پذیرد")
        return value

    @field_validator("payment_gateway")
    @classmethod
    def _supported_payment_gateway(cls, value: str) -> str:
        if value not in {"manual", "mock", "sandbox"}:
            raise ValueError("MP_PAYMENT_GATEWAY باید manual، mock یا sandbox باشد")
        return value

    @model_validator(mode="after")
    def validate_production_configuration(self) -> Settings:
        """Check the final Pydantic Settings object, including values from `.env`.

        Reading ``os.environ`` inside a field validator misses values loaded from
        Pydantic Settings' env file and previously allowed the development key to
        reach a production app.
        """
        if self.environment != "production":
            return self

        problems: list[str] = []
        secret_bytes = len(self.secret_key.encode("utf-8"))
        if secret_bytes < MIN_SECRET_BYTES:
            problems.append(f"MP_SECRET_KEY باید حداقل {MIN_SECRET_BYTES} بایت باشد")
        if self.secret_key == DEFAULT_DEV_SECRET or self.secret_key.lower().startswith(
            ("change-me", "replace-me", "example", "your-secret")
        ):
            problems.append("کلید MP_SECRET_KEY پیش‌فرض/نمونه در production مجاز نیست")

        if not self.biometric_key:
            problems.append("MP_BIOMETRIC_KEY در production الزامی است")
        else:
            try:
                biometric_bytes = base64.b64decode(self.biometric_key, validate=True)
            except (binascii.Error, ValueError):
                problems.append("MP_BIOMETRIC_KEY باید Base64 معتبر باشد")
            else:
                if len(biometric_bytes) != 32:
                    problems.append("MP_BIOMETRIC_KEY باید Base64 از دقیقاً ۳۲ بایت باشد")
                secret_material = self.secret_key.encode("utf-8")
                try:
                    decoded_secret = base64.b64decode(self.secret_key, validate=True)
                except (binascii.Error, ValueError):
                    decoded_secret = b""
                if biometric_bytes in {secret_material, decoded_secret}:
                    problems.append("MP_BIOMETRIC_KEY باید از MP_SECRET_KEY جدا باشد")

        if self.sms_provider == "dev":
            problems.append("MP_SMS_PROVIDER در production نباید dev باشد")
        elif self.sms_provider == "webmagfa":
            for name, value in (
                ("MP_SMS_API_URL", self.sms_api_url),
                ("MP_SMS_USERNAME", self.sms_username),
                ("MP_SMS_PASSWORD", self.sms_password),
                ("MP_SMS_ORIGINATOR", self.sms_originator),
            ):
                if not value:
                    problems.append(f"{name} در production الزامی است")
        else:  # kavenegar
            for name, value in (
                ("MP_SMS_API_URL", self.sms_api_url),
                ("MP_SMS_API_KEY", self.sms_api_key),
                ("MP_SMS_ORIGINATOR", self.sms_originator),
            ):
                if not value:
                    problems.append(f"{name} در production الزامی است")

        if self.sms_provider in {"webmagfa", "kavenegar"}:
            sms_url = urlsplit(self.sms_api_url)
            if (
                sms_url.scheme != "https"
                or not sms_url.hostname
                or sms_url.username is not None
                or sms_url.password is not None
            ):
                problems.append(
                    "MP_SMS_API_URL در production باید HTTPS معتبر و بدون credential باشد"
                )

        valkey_url = urlsplit(self.valkey_url)
        valkey_host = (valkey_url.hostname or "").lower()
        try:
            valkey_is_loopback = ipaddress.ip_address(valkey_host).is_loopback
        except ValueError:
            valkey_is_loopback = valkey_host == "localhost"
        if valkey_url.scheme not in {"redis", "rediss"} or not valkey_host or valkey_is_loopback:
            problems.append("MP_VALKEY_URL باید به Valkey/Redis قابل‌دسترسی production اشاره کند")

        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if not origins or "*" in origins:
            problems.append("MP_CORS_ORIGINS باید allowlist واقعی محیط production باشد")
        else:
            for origin in origins:
                parsed = urlsplit(origin)
                host = (parsed.hostname or "").lower()
                try:
                    host_is_loopback = ipaddress.ip_address(host).is_loopback
                except ValueError:
                    host_is_loopback = host == "localhost"
                if (
                    parsed.scheme != "https"
                    or not host
                    or parsed.username is not None
                    or parsed.password is not None
                    or host_is_loopback
                    or parsed.path not in {"", "/"}
                    or parsed.query
                    or parsed.fragment
                ):
                    problems.append("MP_CORS_ORIGINS باید originهای HTTPS واقعی باشد")
                    break

        if self.payment_gateway == "mock":
            problems.append("MP_PAYMENT_GATEWAY=mock در production مجاز نیست؛ پرداخت حضوری است")
        if self.payment_gateway == "sandbox":
            # بانک صندباکس یک سرویس محلی است؛ اگر کسی آن را به production ببرد، یعنی
            # «تراکنش موفق» را خودمان برای خودمان تأیید می‌کنیم.
            problems.append("بانک صندباکس (MP_PAYMENT_GATEWAY=sandbox) در production مجاز نیست")
        if self.payment_gateway == "manual" and self.payment_sandbox:
            problems.append(
                "MP_PAYMENT_SANDBOX بدون درگاه آنلاین معنا ندارد؛ MP_PAYMENT_SANDBOX=false بگذارید"
            )

        if problems:
            raise ValueError("تنظیمات production نامعتبر: " + "؛ ".join(problems))
        return self


settings = Settings()

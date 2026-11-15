"""تنظیمات بک‌اند — از env / .env خوانده می‌شود (pydantic-settings)."""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# RFC 7518 §3.2 — HMAC-SHA256 با کلید کوتاه‌تر از ۳۲ بایت، امنیت اعلام‌شده را ندارد.
MIN_SECRET_BYTES = 32
DEFAULT_DEV_SECRET = "dev-secret-change-in-production-x"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MP_", extra="ignore")

    app_name: str = "Muscle Paradise"
    environment: str = "development"
    database_url: str = "sqlite:///./mp.db"
    secret_key: str = DEFAULT_DEV_SECRET
    payment_gateway: str = "mock"  # mock | zarinpal
    zarinpal_merchant_id: str = ""
    payment_sandbox: bool = True
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
    valkey_url: str = "redis://localhost:6379/0"
    # allowlist مبدأهای CORS — با کاما جدا شود (env: MP_CORS_ORIGINS)
    # در production باید صریح تنظیم شود؛ خالی = هیچ مبدأ مرورگری (fail-closed)
    cors_origins: str = (
        "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    )
    backend_dir: Path = Path(__file__).resolve().parent.parent

    @field_validator("secret_key")
    @classmethod
    def _secret_key_must_be_strong(cls, v: str) -> str:
        """کلید کوتاه یا پیش‌فرضِ توسعه در production پذیرفته نمی‌شود.

        کشف M48-c2: مقدار پیش‌فرض ۳۱ بایت بود و PyJWT در هر درخواست
        `InsecureKeyLengthWarning` می‌داد — یعنی در لاگ تولید هم می‌آمد.
        این اعتبارسنجی اجازه نمی‌دهد همان اشتباه به production برسد.
        """
        import os

        env = os.getenv("MP_ENVIRONMENT", "development")
        problems = []
        if len(v.encode("utf-8")) < MIN_SECRET_BYTES:
            problems.append(
                f"طول کلید {len(v.encode('utf-8'))} بایت است، حداقل {MIN_SECRET_BYTES} لازم است (RFC 7518)"
            )
        if env == "production" and v == DEFAULT_DEV_SECRET:
            problems.append("کلید پیش‌فرض توسعه در production استفاده شده است")
        if problems and env == "production":
            raise ValueError("secret_key نامعتبر: " + "؛ ".join(problems))
        return v


settings = Settings()

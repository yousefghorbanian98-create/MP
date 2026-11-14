"""تنظیمات بک‌اند — از env / .env خوانده می‌شود (pydantic-settings)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MP_", extra="ignore")

    app_name: str = "Muscle Paradise"
    environment: str = "development"
    database_url: str = "sqlite:///./mp.db"
    secret_key: str = "dev-secret-change-in-production"
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


settings = Settings()

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
    otp_max_attempts: int = 5
    otp_rate_limit: str = "5/minute"
    login_rate_limit: str = "10/minute"
    valkey_url: str = "redis://localhost:6379/0"
    backend_dir: Path = Path(__file__).resolve().parent.parent


settings = Settings()

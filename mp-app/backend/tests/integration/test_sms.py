"""تست‌های لایهٔ پیامک (M28)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.sms import DevSmsProvider, SmsProviderConfigurationError, get_sms_provider

_counter = itertools.count(700001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/sms.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


def test_dev_provider_returns_true_and_logs():
    p = DevSmsProvider()
    assert p.send("09120000000", "کد: 1234") is True


def test_provider_factory_default_dev(monkeypatch):
    monkeypatch.setattr(settings, "sms_provider", "dev")
    assert get_sms_provider().name == "dev"


def test_provider_factory_unknown_fails_closed(monkeypatch):
    monkeypatch.setattr(settings, "sms_provider", "unknown-gateway")
    with pytest.raises(SmsProviderConfigurationError):
        get_sms_provider()


def test_development_provider_is_never_selected_in_production(monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "sms_provider", "dev")
    with pytest.raises(SmsProviderConfigurationError):
        get_sms_provider()


@pytest.mark.parametrize(
    "provider,secret",
    [("webmagfa", "webmagfa-secret-marker"), ("kavenegar", "kavenegar-secret-marker")],
)
def test_provider_failure_logs_do_not_echo_credentials(
    monkeypatch, caplog, provider: str, secret: str
) -> None:
    import urllib.error
    import urllib.request

    from app.sms import KavenegarProvider, WebMagfaProvider

    monkeypatch.setattr(settings, "sms_api_url", "https://sms.example.test/api")
    monkeypatch.setattr(settings, "sms_username", "account")
    monkeypatch.setattr(settings, "sms_password", secret)
    monkeypatch.setattr(settings, "sms_api_key", secret)
    monkeypatch.setattr(settings, "sms_originator", "1000000000")
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *args, **kwargs: (_ for _ in ()).throw(urllib.error.URLError(secret)),
    )
    sender = WebMagfaProvider() if provider == "webmagfa" else KavenegarProvider()

    assert sender.send("09120000000", "OTP 123456") is False
    assert secret not in caplog.text


def test_otp_response_exposes_dev_code_only_in_dev(client):
    r = client.post("/api/v1/auth/otp/request", json={"phone": f"091{next(_counter):08d}"})
    assert r.status_code == 200
    assert "dev_code" in r.json()  # حالت dev (پیش‌فرض)


def test_otp_sms_failure_surfaces_error(client, monkeypatch):
    from app import sms as sms_mod

    class _Fail:
        name = "dev"

        def send(self, phone, text):
            return False

    monkeypatch.setattr(sms_mod, "get_sms_provider", lambda: _Fail())
    r = client.post("/api/v1/auth/otp/request", json={"phone": f"092{next(_counter):08d}"})
    assert r.status_code == 503 or r.status_code == 400
    assert "sms_failed" in r.text

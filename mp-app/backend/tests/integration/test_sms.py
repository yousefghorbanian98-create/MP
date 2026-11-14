"""تست‌های لایهٔ پیامک (M28)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.sms import DevSmsProvider, get_sms_provider

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


def test_provider_factory_unknown_falls_back_to_dev(monkeypatch):
    monkeypatch.setattr(settings, "sms_provider", "unknown-gateway")
    assert get_sms_provider().name == "dev"


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

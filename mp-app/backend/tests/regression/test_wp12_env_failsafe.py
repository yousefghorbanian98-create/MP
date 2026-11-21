"""WP 1.2 / F-02 — محیط fail-safe و نشت dev_code دوشرطی.

ریشهٔ نقص: پیش‌فرض `environment="development"` و `MP_SMS_PROVIDER=dev` بود؛ اگر
استقرار `MP_ENVIRONMENT` را فراموش می‌کرد، پاسخ OTP کد را برمی‌گرداند (ورود بدون پیامک).
قرارداد جدید:
- بدون MP_ENVIRONMENT صریح، create_app خطا می‌دهد (مگر تست خودکار).
- dev_code فقط با environment=development **و** MP_ALLOW_DEV_OTP_ECHO=true.
- در production، MP_ALLOW_DEV_OTP_ECHO=true پیکربندی را رد می‌کند.
"""

from __future__ import annotations

import base64
import sys

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings

from .test_production_ops import valid_production_settings


@pytest.fixture()
def dev_client(tmp_path, monkeypatch):
    from app.config import settings
    from app.main import create_app
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/env.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(create_app()) as c:
        yield c
    reset_engine()


def test_otp_response_has_no_dev_code_by_default(dev_client) -> None:
    r = dev_client.post("/api/v1/auth/otp/request", json={"phone": "09121234501"})
    assert r.status_code == 200
    assert "dev_code" not in r.json()


def test_otp_response_echoes_dev_code_only_with_explicit_flag(dev_client, monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "allow_dev_otp_echo", True)
    r = dev_client.post("/api/v1/auth/otp/request", json={"phone": "09121234502"})
    assert r.status_code == 200
    assert len(r.json()["dev_code"]) == 6


def test_dev_code_echo_is_double_gated_in_service_source() -> None:
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "modules/auth/service.py").read_text(
        encoding="utf-8"
    )
    assert text.count('if provider.name == "dev" and dev_otp_echo_enabled():') == 2
    assert 'out["dev_code"]' in text and 'result["dev_code"]' in text


def test_implicit_environment_refuses_to_start(monkeypatch) -> None:
    import app.main as main_module

    implicit = Settings(_env_file=None, allow_implicit_dev=False)
    assert "environment" not in implicit.model_fields_set
    monkeypatch.setattr(main_module, "settings", implicit)
    with pytest.raises(RuntimeError, match="MP_ENVIRONMENT"):
        main_module.create_app()


def test_explicit_environment_allows_startup(monkeypatch) -> None:
    import app.main as main_module

    explicit = Settings(_env_file=None, environment="development", allow_implicit_dev=False)
    assert "environment" in explicit.model_fields_set
    monkeypatch.setattr(main_module, "settings", explicit)
    main_module._assert_explicit_environment()  # no raise


def test_environment_from_env_var_counts_as_explicit(monkeypatch) -> None:
    monkeypatch.setenv("MP_ENVIRONMENT", "development")
    monkeypatch.setenv("MP_ALLOW_IMPLICIT_DEV", "false")
    s = Settings(_env_file=None)
    assert "environment" in s.model_fields_set


def test_production_rejects_dev_otp_echo() -> None:
    with pytest.raises(ValidationError, match="MP_ALLOW_DEV_OTP_ECHO"):
        valid_production_settings(allow_dev_otp_echo=True)


def test_production_without_echo_is_accepted() -> None:
    assert valid_production_settings().allow_dev_otp_echo is False
    assert base64  # keep import used for fixtures of biometric key


def _load_deploy_gate():
    import importlib.util
    from pathlib import Path

    path = Path(__file__).resolve().parents[2] / "scripts" / "deploy_gate.py"
    spec = importlib.util.spec_from_file_location("deploy_gate_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module  # dataclasses يازمان ثبت ماژول
    spec.loader.exec_module(module)
    return module


def test_deploy_gate_otp_guard_passes_on_repository() -> None:
    gate = _load_deploy_gate()
    report = gate.Report()
    gate.check_otp_echo_guard(report)
    assert report.problems == []
    assert len(report.checks) == 2


def test_deploy_gate_detects_dev_code_in_body() -> None:
    gate = _load_deploy_gate()
    assert gate.otp_body_exposes_dev_code({"dev_code": "123456"}) is True
    assert gate.otp_body_exposes_dev_code({"dev_code": None}) is False
    assert gate.otp_body_exposes_dev_code({"phone": "0912"}) is False

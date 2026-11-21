"""WP 1.3 / F-06 — `/api/v1/metrics` نیازمند Bearer است.

پیش از اصلاح: بدون توکن ۲۰۰ با متریک‌ها (۳۴۶ خط، ۱۲ خانواده).
بعد: توکن تنظیم‌نشده ⇒ ۴۰۳، هدر نبود/توکن غلط ⇒ ۴۰۱، توکن درست ⇒ ۲۰۰.
"""

from __future__ import annotations

import pytest

from app.config import settings

from ._metrics import METRICS_AUTH, METRICS_TOKEN


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.main import create_app
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from fastapi.testclient import TestClient
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/metrics.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(create_app()) as c:
        yield c
    reset_engine()


def test_metrics_without_token_is_rejected(client):
    res = client.get("/api/v1/metrics")
    assert res.status_code == 401
    assert "mp_" not in res.text


def test_metrics_with_wrong_token_is_rejected(client):
    res = client.get("/api/v1/metrics", headers={"Authorization": "Bearer nope"})
    assert res.status_code == 401


def test_metrics_with_non_bearer_scheme_is_rejected(client):
    res = client.get("/api/v1/metrics", headers={"Authorization": f"Basic {METRICS_TOKEN}"})
    assert res.status_code == 401


def test_metrics_with_correct_token_is_served(client):
    res = client.get("/api/v1/metrics", headers=METRICS_AUTH)
    assert res.status_code == 200
    assert "mp_" in res.text


def test_metrics_disabled_when_token_not_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "metrics_token", "")
    res = client.get("/api/v1/metrics", headers=METRICS_AUTH)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "metrics_disabled"


def test_metrics_guard_is_recorded_for_gate(client):
    """گیت guard باید این مسیر را «محافظت‌شده» ببیند، نه عمومی."""
    import importlib.util
    from pathlib import Path

    gate_path = Path(__file__).resolve().parents[2] / "scripts" / "route_guard_gate.py"
    spec = importlib.util.spec_from_file_location("route_guard_gate", gate_path)
    gate = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(gate)
    rows = [r for r in gate.collect_routes(client.app) if r[1].endswith("/api/v1/metrics")]
    assert rows and all("metrics_token" in kinds for _, _, kinds in rows)
    assert ("GET", "/api/v1/metrics") not in gate.PUBLIC

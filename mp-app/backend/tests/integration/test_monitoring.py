"""تست‌های مانیتورینگ (M13) — متریک، readiness، SLO."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    from cache.store import InMemoryCache, reset_cache
    from modules.auth.router import limiter

    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()


def test_metrics_endpoint_exposes_counters(client):
    from app.metrics import metrics

    metrics.inc("mp_test_events_total", tag="x")
    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    assert "mp_test_events_total" in resp.text
    assert 'tag="x"' in resp.text


def test_metrics_histogram_quantiles(client):
    from app.metrics import metrics

    for v in (0.1, 0.5, 1.5, 3.0):
        metrics.observe("mp_demo_seconds", v)
    text = client.get("/api/v1/metrics").text
    assert "mp_demo_seconds_count 4" in text
    assert "mp_demo_seconds_sum" in text
    assert 'quantile="0.99"' in text


def test_checkin_metrics_recorded(client, session, make_member):
    from modules.face_id import service as face_service

    member = make_member()
    face_service.check_in(session, member.id, method="qr")
    text = client.get("/api/v1/metrics").text
    assert "mp_checkins_total" in text


def test_ready_endpoint_and_slo_flag(client):
    body = client.get("/api/v1/health/ready").json()
    assert body["ready"] is True
    assert body["checkin_slo_ok"] in (True, False)


def test_alert_rules_cover_slo_and_down():
    """سناریوی خرابی: آلارم‌ها باید SLO و قطعی را پوشش دهند (بدون Prometheus اجرایی — اعتبارسنجی YAML)."""
    from pathlib import Path

    import yaml

    rules = yaml.safe_load(Path("../infra/monitoring/alerts.yml").read_text())
    names = {r["alert"] for g in rules["groups"] for r in g["rules"]}
    assert {"CheckinSLOBreach", "BackendDown", "High5xxRate", "ValkeyDown"} <= names
    slo = next(r for g in rules["groups"] for r in g["rules"] if r["alert"] == "CheckinSLOBreach")
    assert "0.99" in slo["expr"] and ">= 2" in slo["expr"]

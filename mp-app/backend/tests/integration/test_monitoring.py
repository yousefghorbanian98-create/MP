"""تست‌های مانیتورینگ (M13) — متریک، readiness، SLO."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

from ._metrics import METRICS_AUTH


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
    resp = client.get("/api/v1/metrics", headers=METRICS_AUTH)
    assert resp.status_code == 200
    assert "mp_test_events_total" in resp.text
    assert 'tag="x"' in resp.text


def test_metrics_histogram_uses_prometheus_bucket_exposition(client):
    from app.metrics import metrics

    for v in (0.1, 0.5, 1.5, 3.0):
        metrics.observe("mp_demo_seconds", v)
    text = client.get("/api/v1/metrics", headers=METRICS_AUTH).text
    assert "mp_demo_seconds_count 4.0" in text
    assert "mp_demo_seconds_sum" in text
    assert "mp_demo_seconds_bucket" in text
    assert 'le="+Inf"' in text
    assert "mp_demo_seconds{quantile=" not in text


def test_http_metrics_have_bounded_route_and_status_labels(client):
    client.get("/health")
    text = client.get("/api/v1/metrics", headers=METRICS_AUTH).text
    assert 'mp_http_requests_total{method="GET",route="/health",status="200"}' in text
    assert "mp_http_request_duration_seconds_bucket" in text


def test_request_id_is_generated_validated_and_returned(client):
    import re

    generated = client.get("/health")
    request_id = generated.headers["X-Request-ID"]
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)

    supplied = "123e4567e89b42d3a456426614174000"
    echoed = client.get("/health", headers={"X-Request-ID": supplied})
    assert echoed.headers["X-Request-ID"] == supplied

    invalid = client.get("/health", headers={"X-Request-ID": "not-a-request-id"})
    assert re.fullmatch(r"[0-9a-f]{32}", invalid.headers["X-Request-ID"])
    assert invalid.headers["X-Request-ID"] != "not-a-request-id"


def test_structured_logs_receive_request_id_context():
    from asgi_correlation_id import correlation_id

    from app.logging import add_request_id

    token = correlation_id.set("123e4567e89b42d3a456426614174000")
    try:
        assert add_request_id(None, "info", {}) == {
            "request_id": "123e4567e89b42d3a456426614174000"
        }
    finally:
        correlation_id.reset(token)


def test_prometheus_multiprocess_metrics_are_exposed_from_worker_files(tmp_path):
    import os
    import subprocess
    import sys
    from pathlib import Path

    backend = Path(__file__).resolve().parents[2]
    code = """
from app.metrics import metrics
metrics.inc('mp_worker_events_total', worker='worker-a')
metrics.observe('mp_worker_duration_seconds', 0.25, worker='worker-a')
text = metrics.render()
assert 'mp_worker_events_total{worker=\"worker-a\"} 1.0' in text, text
assert 'mp_worker_duration_seconds_bucket' in text, text
"""
    env = os.environ.copy()
    env["PROMETHEUS_MULTIPROC_DIR"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_checkin_metrics_recorded(client, session, make_member):
    from modules.face_id import service as face_service

    member = make_member()
    face_service.check_in(session, member.id, method="qr")
    text = client.get("/api/v1/metrics", headers=METRICS_AUTH).text
    assert "mp_checkins_total" in text


def test_ready_endpoint_and_slo_flag(client):
    body = client.get("/api/v1/health/ready").json()
    assert body["ready"] is True
    assert body["checkin_slo_ok"] in (True, False)


def test_ready_fails_closed_when_shared_rate_limit_storage_is_unhealthy(client, monkeypatch):
    import modules.auth.router

    monkeypatch.setattr(modules.auth.router, "rate_limit_storage_healthy", lambda: False)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["ready"] is False
    assert response.json()["database_ok"] is True
    assert response.json()["rate_limit_storage_ok"] is False


def test_alert_rules_cover_slo_and_down():
    """سناریوی خرابی: آلارم‌ها باید SLO و قطعی را پوشش دهند (بدون Prometheus اجرایی — اعتبارسنجی YAML)."""
    from pathlib import Path

    import yaml

    # مسیر از فایل، نه از cwd: این تست پیش‌تر فقط وقتی `pytest` از `mp-app/backend`
    # اجرا می‌شد سبز بود و از ریشهٔ مخزن قرمز می‌شد — شکستی که به کد ربطی نداشت و
    # همان چیزی است که خوانندهٔ گیت را بی‌اعتماد می‌کند (شاهد: finn/reports/m97 و
    # m99؛ baseline محلی ۸۶۱/۱ از ریشه در برابر ۸۶۷/۱ از mp-app/backend).
    alerts = Path(__file__).resolve().parents[3] / "infra" / "monitoring" / "alerts.yml"
    rules = yaml.safe_load(alerts.read_text(encoding="utf-8"))
    names = {r["alert"] for g in rules["groups"] for r in g["rules"]}
    assert {"CheckinSLOBreach", "BackendDown", "High5xxRate", "ValkeyDown"} <= names
    slo = next(r for g in rules["groups"] for r in g["rules"] if r["alert"] == "CheckinSLOBreach")
    assert "0.99" in slo["expr"] and ">= 2" in slo["expr"]

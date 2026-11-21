"""فاز ۸ لوپ ۵ — چرخهٔ worker، صف و مشاهده‌پذیری (QF-27).

# قرارداد

| مورد | قاعده |
|---|---|
| heartbeat | هر دور relay زمان `last_seen_at` را به‌روز می‌کند |
| کهنگی | heartbeat قدیمی‌تر از آستانه = worker مرده (`ok=False`)، نه «سالم» |
| متریک | `mp_outbox_pending` / `mp_outbox_dead_letters` / `mp_outbox_oldest_pending_seconds` از DB واقعی |
| redaction | هیچ payload یا متن خطایی در `/metrics` نمی‌آید؛ فقط عدد/برچسب |
| readiness | بدون درخواست worker لازم، ۲۰۰ می‌ماند؛ با `MP_REQUIRE_WORKER=true` و بدون heartbeat ⇒ ۵۰۳ |

# چرا این تست

outbox بدون worker = رویدادهای انباشته که کسی نمی‌بیند. پیش از این، نه
heartbeat بود نه متریک صف؛ «کار می‌کند» فقط یعنی تست‌ها سبزند.

# آنچه تست نمی‌کند
- kill واقعی پروسه در محیط استقرار و هشدار در Prometheus/Alertmanager؛
  قاعدهٔ هشدار فقط مستند می‌شود (`BLOCKED`: سرور پایش بیرونی نیست).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from db.base import get_session_factory
from db.models import OutboxEvent, WorkerHeartbeat
from modules.outbox import health as outbox_health
from modules.outbox.service import enqueue

from ._metrics import METRICS_AUTH


def _enqueue(db, key: str, topic: str = "payment.approved") -> OutboxEvent:
    return enqueue(db, topic=topic, payload={"amount": 1000}, dedup_key=key, commit=False)


def test_relay_cycle_records_fresh_heartbeat(client: TestClient) -> None:
    _ = client
    from jobs import outbox_relay

    outbox_relay.run_once()

    with get_session_factory()() as s:
        row = s.scalar(select(WorkerHeartbeat).where(WorkerHeartbeat.worker_key == "outbox"))
        assert row is not None
        assert row.last_seen_at is not None
        status = outbox_health.worker_status(s)
    assert status["ok"] is True
    assert status["age_seconds"] < 60


def test_stale_heartbeat_is_reported_as_dead(client: TestClient) -> None:
    _ = client
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    with get_session_factory()() as s:
        s.merge(
            WorkerHeartbeat(
                worker_key="outbox",
                started_at=now - timedelta(hours=3),
                last_seen_at=now - timedelta(hours=2),
                last_result="{}",
            )
        )
        s.commit()
        status = outbox_health.worker_status(s, now=now, stale_after_seconds=300)
    assert status["ok"] is False
    assert status["age_seconds"] >= 7200


def test_queue_stats_count_each_state(client: TestClient) -> None:
    _ = client
    now = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
    with get_session_factory()() as s:
        pending = _enqueue(s, "stats-pending")
        pending.available_at = now - timedelta(minutes=5)
        pending.created_at = now - timedelta(minutes=9)
        sending = _enqueue(s, "stats-sending")
        sending.status = "sending"
        dead = _enqueue(s, "stats-dead")
        dead.status = "dead"
        s.commit()
        stats = outbox_health.queue_stats(s, now=now)
    assert stats["pending"] >= 1
    assert stats["sending"] >= 1
    assert stats["dead_letters"] == 0  # dead letter جداست، event مرده شمارش نمی‌شود
    assert stats["oldest_pending_age_seconds"] >= 300


def test_metrics_expose_queue_gauges_without_payload(client: TestClient) -> None:
    _ = client
    with get_session_factory()() as s:
        _enqueue(s, "metrics-visible")
        s.commit()
        outbox_health.refresh_metrics(s)
    from app.metrics import metrics

    rendered = (
        metrics.render().decode() if isinstance(metrics.render(), bytes) else metrics.render()
    )
    assert "mp_outbox_pending" in rendered
    assert "mp_outbox_dead_letters" in rendered
    assert "mp_outbox_oldest_pending_seconds" in rendered
    # redaction: هیچ بدنهٔ رویداد یا متن خطایی نباید در خروجی باشد
    assert "amount" not in rendered
    assert "payment.approved" not in rendered


def test_metrics_endpoint_refreshes_from_database(client: TestClient) -> None:
    with get_session_factory()() as s:
        _enqueue(s, "metrics-endpoint")
        s.commit()
    res = client.get("/api/v1/metrics", headers=METRICS_AUTH)
    assert res.status_code == 200
    assert "mp_outbox_pending" in res.text


def test_readiness_includes_worker_health_only_when_required(
    client: TestClient, monkeypatch
) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "require_worker", False, raising=False)
    body = client.get("/api/v1/health/ready").json()
    assert "worker_ok" not in body
    assert "outbox" in body

    monkeypatch.setattr(settings, "require_worker", True, raising=False)
    with get_session_factory()() as s:
        s.query(WorkerHeartbeat).delete()
        s.commit()
    dead = client.get("/api/v1/health/ready")
    assert dead.status_code == 503
    assert dead.json()["worker_ok"] is False

    with get_session_factory()() as s:
        outbox_health.heartbeat(s, worker_key="outbox", result={"sent": 0})
        s.commit()
    alive = client.get("/api/v1/health/ready")
    assert alive.status_code == 200
    assert alive.json()["worker_ok"] is True

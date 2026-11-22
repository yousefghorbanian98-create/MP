"""WP 2.2 / F‑04 — مشاهده‌پذیری استخر، ۵۰۳ به‌جای ۵۰۰، و قرمزی readiness (D‑13).

قرمز پیش از اصلاح: ماژول `app.pool_metrics` وجود ندارد؛ `TimeoutError` استخر ۵۰۰ می‌دهد.
"""

from __future__ import annotations

import time

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from sqlalchemy.pool import QueuePool

from app import pool_metrics
from app.metrics import Metrics


def _engine(pool_size: int = 2, max_overflow: int = 0, timeout: float = 0.2):
    return create_engine(
        "sqlite:///:memory:",
        poolclass=QueuePool,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=timeout,
    )


def _lines(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for line in text.splitlines():
        if line and not line.startswith("#"):
            name, _, value = line.rpartition(" ")
            out[name] = float(value)
    return out


def test_pool_gauges_follow_checkout_and_checkin():
    """C6: gauges size/checkedout/overflow در /metrics و به‌روز هستند."""
    engine = _engine(pool_size=2, max_overflow=0)
    metrics = Metrics()
    pool_metrics.install_pool_metrics(engine, metrics)

    conn = engine.connect()
    pool_metrics.publish_pool_gauges(engine, metrics)
    values = _lines(metrics.render())
    assert values["mp_db_pool_size"] == 2.0
    assert values["mp_db_pool_checkedout"] == 1.0
    assert values["mp_db_pool_overflow"] == 0.0

    conn.close()
    pool_metrics.publish_pool_gauges(engine, metrics)
    assert _lines(metrics.render())["mp_db_pool_checkedout"] == 0.0


def test_connection_held_histogram_observed_on_checkin():
    """C6: مدت نگه‌داشتن اتصال در histogram ثبت می‌شود."""
    engine = _engine()
    metrics = Metrics()
    pool_metrics.install_pool_metrics(engine, metrics)
    with engine.connect():
        time.sleep(0.01)
    values = _lines(metrics.render())
    assert values["mp_db_connection_held_seconds_count"] == 1.0
    assert values["mp_db_connection_held_seconds_sum"] > 0.0


def test_pool_timeout_is_503_with_retry_after_not_500():
    """C7: TimeoutError استخر ⇒ 503 + Retry-After، کد db_pool_exhausted، نه ۵۰۰."""
    from app.metrics import metrics as global_metrics
    from app.unhandled import register

    app = FastAPI()
    register(app)

    @app.get("/boom")
    def boom() -> None:
        raise PoolTimeoutError("QueuePool limit of size 2 overflow 0 reached", None, None)

    before = _lines(global_metrics.render()).get("mp_db_pool_timeout_total", 0.0)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 503
    assert resp.headers.get("Retry-After") == "1"
    assert resp.json()["error"]["code"] == "db_pool_exhausted"
    after = _lines(global_metrics.render())["mp_db_pool_timeout_total"]
    assert after == before + 1.0


def test_saturation_turns_red_only_after_window():
    """C8: ≥۹۰٪ ظرفیت پیوسته N=۱۰s ⇒ اشباع؛ کمتر از N ⇒ هنوز سبز؛ آزادشدن ⇒ سبز."""
    engine = _engine(pool_size=2, max_overflow=0)
    c1 = engine.connect()
    c2 = engine.connect()
    key = "wp22-test"
    assert pool_metrics.pool_saturated(engine, key=key, now=100.0) is False  # شروع پنجره
    assert pool_metrics.pool_saturated(engine, key=key, now=105.0) is False  # هنوز کمتر از N
    assert pool_metrics.pool_saturated(engine, key=key, now=111.0) is True  # بیش از N
    c1.close()
    c2.close()
    assert pool_metrics.pool_saturated(engine, key=key, now=112.0) is False


def test_saturation_window_constants_are_documented_values():
    """C8: آستانه و پنجره مطابق D‑13 هستند."""
    assert pool_metrics.SATURATION_RATIO == 0.9
    assert pool_metrics.SATURATION_WINDOW_SECONDS == 10.0

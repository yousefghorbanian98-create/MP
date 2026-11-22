"""WP 2.5 / F‑17 — بازتاب شمارندهٔ خطای scrape در `/health/ready`.

کیت: `api/v1/monitoring.py` ⇒ `mp_metrics_scrape_errors_total` و بازتاب در `/health/ready`.
"""

from __future__ import annotations


def test_ready_reports_scrape_error_count(client) -> None:
    from api.v1 import monitoring

    before = client.get("/api/v1/health/ready").json()["metrics_scrape_errors"]
    monitoring._log_scrape_failure()
    after = client.get("/api/v1/health/ready").json()["metrics_scrape_errors"]
    assert after == before + 1

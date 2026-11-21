"""WP 2.5 / F‑17 — خطای «بی‌صدا» باید ثبت و شمارش شود.

- ردیف JP7 خراب: هشدار لاگ + شمارنده، نه `continue` بی‌صدا.
- خطای scrape متریک: شمارنده افزایش یابد (علاوه بر لاگ debug).
- نگهبان: در کد تولید هیچ except بدون لاگ/شمارنده نباشد.
"""

from __future__ import annotations

import ast
import logging
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.metrics import metrics

BACKEND = Path(__file__).resolve().parents[2]
_LOG_OR_COUNT = {"debug", "info", "warning", "error", "exception", "critical", "inc"}
PROD_DIRS = ("app", "api", "modules", "engine", "security", "db", "jobs", "cache")


def _counter_value(name: str) -> float:
    for line in metrics.render().splitlines():
        if line.startswith(name + " ") or line.startswith(name + "{"):
            return float(line.rsplit(" ", 1)[1])
    return 0.0


def test_jp7_unreadable_row_is_logged_and_counted(monkeypatch, caplog) -> None:
    import app.security.ownership as ownership
    from modules.assessment import service

    monkeypatch.setattr(ownership, "ensure_member_scope", lambda *a, **k: None)
    rows = [
        SimpleNamespace(
            id=1,
            skinfolds_mm='{"chest": 10, "abdomen": 12}',
            measured_at=datetime(2026, 1, 1, tzinfo=UTC),
            body_fat_pct=None,
        ),
        SimpleNamespace(id=2, skinfolds_mm="{not json", measured_at=None, body_fat_pct=None),
        SimpleNamespace(
            id=3,
            skinfolds_mm='{"chest": 8, "abdomen": 9}',
            measured_at=datetime(2026, 2, 1, tzinfo=UTC),
            body_fat_pct=None,
        ),
    ]
    db = SimpleNamespace(scalars=lambda _stmt: SimpleNamespace(all=lambda: rows))

    before = _counter_value("assessment_jp7_rows_skipped_total")
    with caplog.at_level(logging.WARNING):
        result = service.jp7_trend(db, member_id=7, user=None)

    assert [p["id"] for p in result["measurements"]] == [1, 3]
    assert _counter_value("assessment_jp7_rows_skipped_total") == before + 1
    assert any("JP7" in r.getMessage() and r.levelno == logging.WARNING for r in caplog.records)


def test_scrape_failure_is_counted(monkeypatch) -> None:
    from api.v1 import monitoring

    before = _counter_value("mp_metrics_scrape_failures_total")
    monitoring._log_scrape_failure()
    assert _counter_value("mp_metrics_scrape_failures_total") == before + 1


def _is_silent(handler: ast.ExceptHandler) -> bool:
    for stmt in handler.body:
        if isinstance(stmt, (ast.Pass, ast.Continue)):
            continue
        if isinstance(stmt, ast.Return) and stmt.value is None:
            continue
        return False
    for stmt in handler.body:
        for node in ast.walk(stmt):
            is_log_call = (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _LOG_OR_COUNT
            )
            if is_log_call:
                return False
    return True


def test_no_silent_except_in_production_code() -> None:
    offenders: list[str] = []
    for d in PROD_DIRS:
        for path in sorted((BACKEND / d).rglob("*.py")):
            if "__pycache__" in path.parts or "migrations" in path.parts:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and _is_silent(node):
                    rel = path.relative_to(BACKEND)
                    offenders.append(f"{rel}:{node.lineno}")
    assert offenders == []


@pytest.mark.parametrize("name", ["mp_metrics_scrape_failures_total"])
def test_counter_names_are_exported(name: str) -> None:
    # شمارنده قبل از اولین افزایش هم باید در خروجی /metrics نمونه‌ای داشته باشد.
    metrics.inc("mp_metrics_scrape_failures")
    assert name in metrics.render()

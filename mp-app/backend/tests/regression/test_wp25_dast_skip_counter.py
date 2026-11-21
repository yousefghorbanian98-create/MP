"""WP 2.5 / F‑17 — ردّ عملیات در DAST باید شمارنده داشته باشد (`mp_dast_errors_total`)."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from app.metrics import metrics

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "dast.py"


def _load_dast():
    name = "dast_under_test"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_dast_skip_increments_counter() -> None:
    dast = _load_dast()
    before = metrics.render()
    dast._log_skip("operation")
    after = metrics.render()
    assert "mp_dast_errors_total" in after
    assert _count(after) == _count(before) + 1


def _count(text: str) -> float:
    total = 0.0
    for line in text.splitlines():
        if line.startswith("mp_dast_errors_total"):
            total += float(line.rsplit(" ", 1)[1])
    return total

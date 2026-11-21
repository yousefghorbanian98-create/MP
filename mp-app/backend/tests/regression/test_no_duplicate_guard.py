"""WP 0.3 / F-13 — هیچ مسیری دو گارد هم‌نوع (مثلاً دو `permission`) نداشته باشد.

لایه‌بندی متفاوت مجاز است (مثلاً `permission` روی روتر + `grant:*` روی مسیر)،
چون هر کدام مجوز متفاوتی را می‌سنجد. تکرار هم‌نوع فقط هزینهٔ دوبارهٔ enforce
می‌افزاید و همان ریشهٔ F-13 است.
"""

from __future__ import annotations

import importlib.util
import sys
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def _gate():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    spec = importlib.util.spec_from_file_location(
        "route_guard_gate", BACKEND / "scripts" / "route_guard_gate.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _labels(dependant, out: list[str]) -> list[str]:
    kind = getattr(dependant.call, "__rbac__", None)
    if kind:
        out.append(kind)
    for sub in dependant.dependencies:
        _labels(sub, out)
    return out


def test_no_route_has_same_kind_guard_twice():
    gate = _gate()
    from app.main import create_app

    app = create_app()
    duplicates = []
    for prefix, route in gate._walk(app.routes):
        counts = Counter(_labels(route.dependant, []))
        same_kind = {k: n for k, n in counts.items() if n > 1}
        if same_kind:
            duplicates.append(f"{sorted(route.methods)[0]} {prefix + route.path} {same_kind}")
    assert duplicates == [], "گارد هم‌نوع تکراری: " + "; ".join(duplicates)

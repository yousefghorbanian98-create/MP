"""WP 0.6 / F‑24 — ثابت منسوخ و شمارش مسیرها از OpenAPI.

۱) `status.HTTP_422_UNPROCESSABLE_ENTITY` منسوخ است؛ در `app/` و `scripts/` نباید باشد (عدد ۴۲۲ مستقیم).
۲) شمارش مسیرها از OpenAPI: ۱۴۱ مسیر و ۱۶۳ عملیات، و پیمایشگر `route_guard_gate` باید دقیقاً همان مجموعه را ببیند.
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[2]
SCAN_DIRS = [BACKEND / "app", BACKEND / "scripts"]
DEPRECATED = "HTTP_422_UNPROCESSABLE_ENTITY"


def _py_files():
    for d in SCAN_DIRS:
        yield from d.rglob("*.py")


def test_no_deprecated_422_constant() -> None:
    hits = []
    for path in _py_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == DEPRECATED:
                hits.append(f"{path.relative_to(BACKEND)}:{node.lineno}")
            if isinstance(node, ast.Name) and node.id == DEPRECATED:
                hits.append(f"{path.relative_to(BACKEND)}:{node.lineno}")
    assert not hits, f"ثابت منسوخ هنوز استفاده می‌شود: {hits}"


def _gate():
    spec = importlib.util.spec_from_file_location(
        "route_guard_gate", BACKEND / "scripts" / "route_guard_gate.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def openapi_ops():
    from app.main import create_app

    spec = create_app().openapi()
    ops = {
        (m.upper(), p)
        for p, item in spec["paths"].items()
        for m in item
        if m in ("get", "post", "put", "patch", "delete")
    }
    return len(spec["paths"]), ops


def test_openapi_counts_are_141_paths_163_ops(openapi_ops) -> None:
    n_paths, ops = openapi_ops
    assert n_paths == 141
    assert len(ops) == 163


def test_route_walker_matches_openapi(openapi_ops) -> None:
    from app.main import create_app

    _, oa_ops = openapi_ops
    gate = _gate()
    walked = set()
    for prefix, r in gate._walk(create_app().routes):
        for m in getattr(r, "methods", set()) or set():
            if m not in ("HEAD", "OPTIONS"):
                walked.add((m, prefix + r.path))
    assert walked == oa_ops, (
        f"فقط در پیمایش: {sorted(walked - oa_ops)[:5]}؛ فقط در OpenAPI: {sorted(oa_ops - walked)[:5]}"
    )

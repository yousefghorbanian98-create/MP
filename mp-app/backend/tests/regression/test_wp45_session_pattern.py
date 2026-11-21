"""WP 4.5 (F‑21) — الگوی session در اسکریپت‌ها یکدست باشد.

قبل از اصلاح: پنج اسکریپت `session = get_session_factory()()` را بیرون از
`with` باز می‌کردند و در `finally: session.close()` می‌بستند. این نشت واقعی
نبود (بستن درست بود)، ولی الگو ناهمگون بود و هر اسکریپت جدید می‌توانست آن را تکرار کند.
بعد از اصلاح: همهٔ این پنج اسکریپت `with get_session_factory()() as session:` دارند.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
TARGETS = [
    "build_progressions.py",
    "import_exercise_catalog.py",
    "seed_criteria.py",
    "seed_norms.py",
    "tag_axis_coverage.py",
]


def _manual_session_lines(tree: ast.AST) -> list[int]:
    """انتساب `x = get_session_factory()()` بیرون از `with`."""
    with_items: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            for item in node.items:
                with_items.add(id(item.context_expr))
    bad: list[int] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if id(call) in with_items:
            continue
        inner = call.func
        if isinstance(inner, ast.Call) and getattr(inner.func, "id", "") == "get_session_factory":
            bad.append(node.lineno)
    return bad


@pytest.mark.parametrize("name", TARGETS)
def test_script_uses_with_block_for_session(name: str) -> None:
    tree = ast.parse((SCRIPTS / name).read_text(encoding="utf-8"))
    assert _manual_session_lines(tree) == [], f"{name}: session بیرون از with"

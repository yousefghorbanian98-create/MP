"""WP 0.4 / F‑07 — آستانه‌های پوشش هر دایرکتوری (scripts/coverage_gate.py).

این تست آستانه‌ها را به عدد بریف قفل می‌کند؛ هر پایین‌آوردن آستانه این تست را می‌شکند.
"""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import pytest

GATE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "coverage_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("coverage_gate", GATE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_thresholds_match_brief() -> None:
    gate = _load()
    assert gate.THRESHOLDS == {
        "modules": 90.0,
        "app": 92.0,
        "api": 90.0,
        "engine": 95.0,
        "security": 95.0,
        "db": 80.0,
        "jobs": 80.0,
        "cache": 75.0,
        "scripts": 60.0,
    }


def _xml(tmp_path: Path, classes: str) -> Path:
    path = tmp_path / "coverage.xml"
    path.write_text(
        textwrap.dedent(
            f"""\
            <?xml version="1.0" ?>
            <coverage><packages><package name="p"><classes>{classes}</classes></package></packages></coverage>
            """
        ),
        encoding="utf-8",
    )
    return path


def _cls(filename: str, hits: list[int]) -> str:
    lines = "".join(f'<line number="{i + 1}" hits="{h}"/>' for i, h in enumerate(hits))
    return f'<class filename="{filename}"><lines>{lines}</lines></class>'


def test_aggregate_buckets_by_top_level_directory(tmp_path: Path) -> None:
    gate = _load()
    xml = _xml(
        tmp_path,
        _cls("db/a.py", [1, 0, 1, 1])
        + _cls("db/b.py", [0, 0])
        + _cls("tests/test_x.py", [1, 1, 1])
        + _cls("main.py", [1]),
    )
    totals = gate.aggregate(xml)
    assert totals["db"] == {"lines": 6, "covered": 3}
    assert "tests" not in totals
    assert totals[gate.ROOT_BUCKET] == {"lines": 1, "covered": 1}


def test_evaluate_fails_below_threshold_and_on_missing_directory() -> None:
    gate = _load()
    totals = {name: {"lines": 100, "covered": 100} for name in gate.THRESHOLDS}
    totals["db"] = {"lines": 100, "covered": 79}  # 79 < 80
    del totals["scripts"]  # بدون داده ⇒ شکست
    failures, table = gate.evaluate(totals)
    assert any(f.startswith("db:") for f in failures)
    assert any(f.startswith("scripts:") for f in failures)
    assert table["db"]["percent"] == 79.0


def test_evaluate_passes_at_exact_threshold() -> None:
    gate = _load()
    totals = {name: {"lines": 100, "covered": int(v)} for name, v in gate.THRESHOLDS.items()}
    failures, _ = gate.evaluate(totals)
    assert failures == []


@pytest.mark.parametrize("name", ["db", "scripts"])
def test_low_directories_are_not_hidden_by_total(name: str) -> None:
    """F‑07: میانگین کل نباید یک دایرکتوری ضعیف را پنهان کند."""
    gate = _load()
    totals = {n: {"lines": 1000, "covered": 1000} for n in gate.THRESHOLDS}
    totals[name] = {"lines": 1000, "covered": 0}
    failures, _ = gate.evaluate(totals)
    assert any(f.startswith(f"{name}:") for f in failures)

"""تست هارنس تجویز (M38-c3) — صفر نقض."""

from __future__ import annotations

from eval.prescription_eval import run_prescription_eval


def test_prescription_eval_zero_violations() -> None:
    result = run_prescription_eval()
    assert result["failed"] == 0, result["checks"]
    names = {check["name"] for check in result["checks"]}
    assert names == {"axis_coverage", "population_gates", "load_accounting"}

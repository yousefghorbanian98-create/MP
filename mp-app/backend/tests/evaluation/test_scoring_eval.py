"""تست هارنس امتیازدهی (M35-c3) — هیچ سناریویی نباید شکست بخورد."""

from __future__ import annotations

from eval.scoring_eval import run_scoring_eval


def test_scoring_eval_all_checks_pass() -> None:
    result = run_scoring_eval()
    assert result["failed"] == 0, result["checks"]
    names = {check["name"] for check in result["checks"]}
    assert names == {
        "round_trip_documented_points",
        "bounds_and_monotonic",
        "sparse_never_exact",
        "sdc_gate",
    }
    assert result["norm_rows"] == 70

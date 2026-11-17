"""تست‌های هارنس ارزیابی — گیت‌های ایمنی/ساختار در CI (G4)."""

from __future__ import annotations

from eval.harness import run_all
from eval.run_eval import main, to_markdown
from eval.scenarios import SCENARIOS


def test_harness_zero_safety_violations():
    r = run_all()
    assert r["safety_population_violations"] == []
    assert r["safety_constraint_violations"] == []
    assert r["library_integrity_problems"] == []
    assert r["structural_problems"] == []


def test_harness_determinism_and_gold_agreement():
    r = run_all()
    assert r["determinism_pass"] is True
    assert r["gold_agreement"]["pct"] >= 95.0


def test_scenarios_cover_matrix():
    sids = {s.sid for s in SCENARIOS}
    # پوشش چهار هدف × سه سطح + محدودیت‌ها + گیت‌ها
    for goal in ("hypertrophy", "strength", "weight_loss", "fitness"):
        for level in ("beginner", "intermediate", "advanced"):
            assert f"{goal}-{level}-3d" in sids
    for c in ("knee", "shoulder", "lower_back", "wrist"):
        assert f"constraint-{c}" in sids
    assert len([s for s in SCENARIOS if s.expect == "block"]) == 7


def test_report_generation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("sys.argv", ["run_eval"])
    main()
    out = tmp_path / "finn" / "reports" / "eval"
    assert (out / "eval-report.json").exists()
    assert (out / "eval-report.md").exists()
    r = run_all()
    md = to_markdown(r, "آزمون")
    assert "توافق با استاندارد طلایی" in md

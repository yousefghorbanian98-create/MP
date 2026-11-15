"""سناریوهای ارزیابی تجویز محور-آگاه — گسترش G4 (M38-c3).

سه محور: (۱) پوشش محورها (direct همیشه حرکت یا شکاف صریح)، (۲) ایمنی
(refer/unknown هرگز تجویز نمی‌گیرند — بازاعتبارسنجی گیت جمعیتی)، (۳) حسابداری بار
(خستگی یک‌بار + بودجه). خروجی JSON در finn/reports/eval.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.axis_prescription import prescribe_axis_work  # noqa: E402
from engine.axis_rules import decide_axis  # noqa: E402

REPORTS = Path(__file__).resolve().parents[3] / "finn" / "reports" / "eval"

CATALOG = [
    {"external_id": "pushup-l1", "name_fa": "شنای سوئدی سطح ۱", "axis_coverage": {"3": 0.7, "5": 0.6, "7": 0.4}, "level": 1},
    {"external_id": "plank", "name_fa": "پلانک", "axis_coverage": {"7": 0.9, "5": 0.5}, "level": 1},
    {"external_id": "deadlift", "name_fa": "ددلیفت", "axis_coverage": {"9": 0.8, "3": 0.7, "10": 0.4}, "level": 2},
    {"external_id": "stretch", "name_fa": "کشش", "axis_coverage": {"1": 0.9, "6": 0.4}, "level": 1},
    {"external_id": "run", "name_fa": "دو", "axis_coverage": {"4": 0.8, "5": 0.3}, "level": 1},
]


def run_prescription_eval() -> dict:
    checks: list[dict] = []
    failed = 0

    # (۱) پوشش: هر direct یا حرکت دارد یا شکاف صریح؛ هر refer/unknown بدون حرکت
    scores = {1: 30, 2: 80, 3: 25, 4: 85, 5: 50, 6: 60, 7: 35, 8: 55, 9: 88, 10: 45}
    scores = {axis: decide_axis(axis=axis, score=s) for axis, s in scores.items()}
    scores[11] = decide_axis(axis=11, score=50, red_flag="تنگی نفس")  # refer
    result = prescribe_axis_work(decisions=scores, movements=CATALOG)
    coverage_errors = []
    for plan in result["axis_plans"]:
        if plan["state"] == "direct" and not plan["movement_ids"] and "شکاف" not in plan["reason"]:
            coverage_errors.append(f"axis {plan['axis']}: direct بدون حرکت/شکاف")
        if plan["state"] in ("refer", "unknown") and plan["movement_ids"]:
            coverage_errors.append(f"axis {plan['axis']}: {plan['state']} با حرکت تجویزشده!")
    checks.append({"name": "axis_coverage", "passed": not coverage_errors, "errors": coverage_errors[:5]})

    # (۲) بازاعتبارسنجی گیت جمعیتی: مسیر ارجاع هرگز تجویز نمی‌گیرد
    gate_errors = []
    for flag in ("درد قفسه سینه", "بارداری", "آسیب حاد زانو"):
        dec = {3: decide_axis(axis=3, score=20), 7: decide_axis(axis=7, score=20, red_flag=flag)}
        r = prescribe_axis_work(decisions=dec, movements=CATALOG)
        plan7 = [p for p in r["axis_plans"] if p["axis"] == 7][0]
        if plan7["movement_ids"]:
            gate_errors.append(f"red-flag «{flag}» تجویز گرفت")
    checks.append({"name": "population_gates", "passed": not gate_errors, "errors": gate_errors[:5]})

    # (۳) حسابداری بار: خستگی یک‌بار + بودجه
    load_errors = []
    if result["load"]["total_fatigue"] != sum(m["sets"] for m in result["selected"]):
        load_errors.append("خستگی ≠ جمع ست‌ها (دوباره‌شماری؟)")
    # بودجهٔ تنگ: بالاتر از کف ست‌های مستقیم (هرگز بریده نمی‌شوند) ولی کمتر از کل
    direct_floor = sum(
        m["sets"] for m in result["selected"] if m["sets"] >= 3
    )
    tight_budget = direct_floor + 1.0
    tight = prescribe_axis_work(decisions=scores, movements=CATALOG, fatigue_budget=tight_budget)
    if tight["load"]["total_fatigue"] > tight_budget:
        load_errors.append("بودجهٔ خستگی رعایت نشد")
    if not tight["trimmed"] and result["load"]["total_fatigue"] > tight_budget:
        load_errors.append("برش بودجه ثبت نشد")
    checks.append({"name": "load_accounting", "passed": not load_errors, "errors": load_errors[:5]})

    for check in checks:
        if not check["passed"]:
            failed += 1
    return {
        "checks": checks,
        "passed": len(checks) - failed,
        "failed": failed,
        "rule_version": "g4-prescription-1.0",
    }


def main() -> int:
    result = run_prescription_eval()
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "2026-11-14-m38c3-prescription-eval.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "failed": result["failed"]}, ensure_ascii=False))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

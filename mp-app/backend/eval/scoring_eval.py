"""سناریوهای ارزیابی موتور امتیازدهی — گسترش G4 (M35-c3).

سه محور اندازه‌گیری: (۱) قطعیت (round-trip روی نقاط مستند)، (۲) محدوده‌ها (۰..۱۰۰)،
(۳) صداقت کیفیت (جدول ناقص هرگز exact جعل نمی‌شود). خروجی JSON در finn/reports/eval.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine.scoring import estimate_percentile, is_real_change
from scripts.seed_norms import NORMS

REPORTS = Path(__file__).resolve().parents[3] / "finn" / "reports" / "eval"


def run_scoring_eval() -> dict:
    checks: list[dict] = []
    failed = 0

    # (۱) قطعیت: هر نقطهٔ مستند باید دقیقاً همان درصدک را برگرداند
    round_trip_errors = []
    for row in NORMS:
        for key, value in row.percentiles.items():
            est = estimate_percentile(
                raw_value=value, percentiles=row.percentiles, direction=row.direction
            )
            expected = float(key) if row.direction == "higher_better" else 100.0 - float(key)
            if est["percentile"] != expected:
                round_trip_errors.append(
                    f"{row.test_key}/{row.sex}/{row.age_min}-{row.age_max}: "
                    f"raw={value} → {est['percentile']} != {expected}"
                )
    checks.append(
        {
            "name": "round_trip_documented_points",
            "passed": not round_trip_errors,
            "errors": round_trip_errors[:5],
        }
    )

    # (۲) محدوده‌ها و اکوتونی: نمره همیشه ۰..۱۰۰؛ برای higher_better صعودی، برای lower_better نزولی
    bounds_errors = []
    for row in NORMS:
        lo = min(float(v) for v in row.percentiles.values())
        hi = max(float(v) for v in row.percentiles.values())
        prev = -1.0
        for step in range(21):
            raw = lo - (hi - lo) * 0.2 + (hi - lo) * 1.4 * step / 20
            est = estimate_percentile(
                raw_value=raw, percentiles=row.percentiles, direction=row.direction
            )
            if not 0 <= est["percentile"] <= 100:
                bounds_errors.append(f"{row.test_key}: {est['percentile']} out of bounds")
            if row.direction == "higher_better" and est["percentile"] < prev:
                bounds_errors.append(f"{row.test_key}: non-monotonic at raw={raw}")
            if row.direction == "lower_better" and prev >= 0 and est["percentile"] > prev:
                bounds_errors.append(f"{row.test_key}: non-monotonic (lower_better) at raw={raw}")
            prev = est["percentile"]
    checks.append(
        {"name": "bounds_and_monotonic", "passed": not bounds_errors, "errors": bounds_errors[:5]}
    )

    # (۳) صداقت کیفیت: جدول ناقص (فقط ۲۵/۷۵) هرگز exact نمی‌گوید
    sparse_errors = []
    for row in NORMS:
        if set(row.percentiles) == {"25", "75"}:
            for raw in (row.percentiles["25"], (row.percentiles["25"] + row.percentiles["75"]) / 2):
                est = estimate_percentile(raw_value=raw, percentiles=row.percentiles)
                if est["quality"] in ("exact", "interpolated"):
                    sparse_errors.append(f"{row.test_key}: sparse labeled {est['quality']}")
    checks.append(
        {"name": "sparse_never_exact", "passed": not sparse_errors, "errors": sparse_errors[:5]}
    )

    # (۴) گیت SDC
    sdc_pairs = [
        (20, 22, 9.0, False),
        (20, 30, 9.0, True),
        (20, 25, 5.0, True),
        (20, 23, 5.0, False),
    ]
    sdc_errors = []
    for old, new, sdc, expected in sdc_pairs:
        result = is_real_change(old_value=old, new_value=new, sdc=sdc)
        if result["real_change"] is not expected:
            sdc_errors.append(f"{old}→{new} sdc={sdc}: {result['real_change']} != {expected}")
    checks.append({"name": "sdc_gate", "passed": not sdc_errors, "errors": sdc_errors[:5]})

    for check in checks:
        if not check["passed"]:
            failed += 1
    return {
        "checks": checks,
        "passed": len(checks) - failed,
        "failed": failed,
        "norm_rows": len(NORMS),
        "rule_version": "g4-scoring-1.0",
    }


def main() -> int:
    result = run_scoring_eval()
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / "2026-11-14-m35c3-scoring-eval.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "failed": result["failed"]}, ensure_ascii=False))
    return 0 if result["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""B5 / WP 4.1 (F-15) — مشخصه‌یابی `prescribe_axis_work` از رفتار HEAD.

fixture: `fixtures/axis_prescription_golden.json` روی HEAD (`c3d28d8`) با seed ثابت ساخته شد.
هر نمونه ورودی و خروجیِ دقیق (یا خطای ApiError با کد و پیام) را نگه می‌دارد.
این آزمون رفتار را قفل می‌کند؛ رفتار جدیدی اضافه نمی‌کند و ادعای قرمزی ندارد.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from app.errors import ApiError
from engine.axis_prescription import prescribe_axis_work

GOLDEN = Path(__file__).parent / "fixtures" / "axis_prescription_golden.json"
SAMPLES = 300
SEED = 46
STATES = ["direct", "maintain", "covered", "refer", "unknown", "other"]


def _cases(n: int = SAMPLES, seed: int = SEED):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        axes = rnd.sample(range(6), k=rnd.randint(1, 6))
        decisions = {a: {"state": rnd.choice(STATES), "reason": f"r{a}"} for a in axes}
        movements = []
        for i in range(rnd.randint(0, 9)):
            coverage = {
                str(a): round(rnd.choice([0.0, 0.2, 0.3, 0.45, 0.5, 0.7, 1.0]), 2)
                for a in rnd.sample(range(6), k=rnd.randint(1, 4))
            }
            movements.append(
                {
                    "external_id": f"m{rnd.randint(0, 6)}-{i}",
                    "name_fa": f"حرکت {i}",
                    "intensity_band": rnd.choice(["low", "mid", "high"]),
                    "progression_key": f"p{i % 3}",
                    "level": rnd.randint(1, 5),
                    "axis_coverage": coverage,
                }
            )
        budget = rnd.choice([3.0, 6.0, 14.0, 40.0])
        out.append(
            {
                "decisions": {str(k): v for k, v in decisions.items()},
                "movements": movements,
                "fatigue_budget": budget,
            }
        )
    return out


def _run(case: dict):
    decisions = {int(k): v for k, v in case["decisions"].items()}
    try:
        result = prescribe_axis_work(
            decisions=decisions, movements=case["movements"], fatigue_budget=case["fatigue_budget"]
        )
    except ApiError as exc:
        return {"error": exc.code, "message": str(exc)}
    return {"result": json.loads(json.dumps(result, ensure_ascii=False, sort_keys=True))}


def test_outputs_match_golden():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    cases = _cases()
    assert len(golden) == len(cases) == SAMPLES
    mismatches = []
    for case, expected in zip(cases, golden, strict=True):
        got = _run(case)
        if got != expected["outcome"]:
            mismatches.append(case)
    assert mismatches == [], f"{len(mismatches)} تفاوت از golden"


def test_golden_covers_success_and_errors():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    kinds = {("error" if "error" in e["outcome"] else "result") for e in golden}
    assert kinds == {"error", "result"}
    trimmed = sum(
        1 for e in golden if "result" in e["outcome"] and e["outcome"]["result"]["trimmed"]
    )
    assert trimmed > 0, "هیچ نمونه‌ای بریدن بودجه را فعال نکرد"

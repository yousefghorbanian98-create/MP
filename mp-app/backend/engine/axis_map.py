"""نگاشت آزمون←محور و تجمیع نمرهٔ محور — نسخهٔ `axis-test-map-1.0` (M36-c2).

قاعده: نمرهٔ هر محور = میانگین وزنی درصدک آزمون‌های مپ‌شدهٔ آن.
محور بدون آزمون داده‌دار ← score=None (missing) — «داده ناشناخته است نه صفر».
تست‌های percentile ← درصدک؛ تست‌های criterion (rubric) ← همان امتیاز ۰..۱۰۰ (کیفیت criterion).
"""

from __future__ import annotations

AXIS_MAP_VERSION = "axis-test-map-1.0"

# axis → [(test_key, weight)] — وزن‌ها جمعشان ۱ (کارشناسی/نسخه‌دار)
AXIS_TEST_MAP: dict[int, tuple[tuple[str, float], ...]] = {
    1: (("sit_and_reach", 1.0),),
    2: (("rubric_balance", 1.0),),
    3: (("pushup_1min", 0.7), ("grip_kg", 0.3)),
    4: (("cooper_1_5mile_sec", 1.0),),
    5: (("pushup_1min", 1.0),),
    6: (("rubric_posture", 1.0),),
    7: (("plank_secs", 1.0),),
    8: (("rubric_coordination", 1.0),),
    9: (("rubric_lifting", 1.0),),
    10: (("grip_kg", 1.0),),
    11: (("rubric_breath", 1.0),),
    12: (("rubric_recovery", 1.0),),
    13: (("rubric_body_awareness", 1.0),),
    14: (("rubric_foundational", 1.0),),
}


def aggregate_axis_scores(test_scores: dict[str, dict]) -> dict[int, dict]:
    """تجمیع نمرهٔ محورها از نمرهٔ آزمون‌ها.

    test_scores: {test_key: {"score": float, "quality": str, "method": "percentile"|"criterion"}}
    خروجی: {axis: {"score": float|None, "quality": str}}
    """
    out: dict[int, dict] = {}
    for axis, mapping in sorted(AXIS_TEST_MAP.items()):
        weighted: list[tuple[float, str]] = []
        for test_key, weight in mapping:
            entry = test_scores.get(test_key)
            if entry and entry.get("score") is not None:
                weighted.append((float(entry["score"]) * weight, entry.get("quality", "")))
        total_weight = sum(
            weight for test_key, weight in mapping if test_scores.get(test_key, {}).get("score") is not None
        )
        if not weighted or total_weight <= 0:
            out[axis] = {"score": None, "quality": "missing"}
            continue
        score = round(sum(value for value, _ in weighted) / total_weight, 1)
        qualities = {quality for _, quality in weighted}
        quality = "mixed" if len(qualities) > 1 else (next(iter(qualities)) or "unknown")
        out[axis] = {"score": score, "quality": quality}
    return out

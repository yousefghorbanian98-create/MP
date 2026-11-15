"""موتور امتیازدهی آزمون‌های میدانی — نسخهٔ `axis-score-1.0` (M35-c2).

نگاشت: مقدار خام ← درصدک (برآورد خطی بین نقاط مستند) ← نمرهٔ ۰ تا ۱۰۰.
نمره = درصدک (تعریف شفاف: «نسبت به جمعیت مرجع») + برچسب کیفیت (E02):
    exact          ← درست روی یک نقطهٔ مستند
    interpolated   ← بین دو نقطهٔ مستند
    range_estimate ← جدول ناقص (فقط ۲۵/۷۵) — تخمین بازه‌ای، نه صدک دقیق
    clamped        ← بیرون از پوشش جدول (لبه‌ها)
گیت «تغییر واقعی» (SDC): تفاوت کمتر از SDC = نویز بازتست، نه بهبود/افت.
هیچ عددی بدون جدول نُرم (M35-c1) محاسبه نمی‌شود (E13).
"""

from __future__ import annotations

from app.errors import ApiError

SCORE_VERSION = "axis-score-1.0"

VALID_PERCENTILE_KEYS = {"5", "25", "50", "75", "95"}
KNOWN_KEYS_ORDER = ["5", "25", "50", "75", "95"]


def _points(percentiles: dict, direction: str) -> list[tuple[float, float]]:
    """نقاط مستند: (مقدار، درصدک) — برای lower_better ترتیب معکوس می‌شود."""
    items = sorted(
        ((float(value), float(key)) for key, value in percentiles.items()),
        key=lambda pair: pair[0],
        reverse=(direction == "lower_better"),
    )
    return items


def estimate_percentile(
    *,
    raw_value: float,
    percentiles: dict,
    direction: str = "higher_better",
) -> dict:
    """برآورد درصدک + کیفیت — جدول ناقص هرگز «دقیق» جعل نمی‌شود."""
    if not percentiles:
        raise ApiError("جدول نُرم خالی است — داده ناشناخته است نه صفر", code="missing_norms")
    if not set(percentiles) <= VALID_PERCENTILE_KEYS:
        raise ApiError("کلیدهای درصدک نامعتبر — فقط 5/25/50/75/95", code="invalid_norms")
    if raw_value is None or not isinstance(raw_value, (int, float)) or isinstance(raw_value, bool):
        raise ApiError("مقدار خام نامعلوم است — داده ناشناخته است نه صفر", code="invalid_raw")
    if direction not in ("higher_better", "lower_better"):
        raise ApiError("direction نامعتبر", code="invalid_direction")

    pts = _points(percentiles, direction)
    sparse = set(percentiles) == {"25", "75"}
    exact_keys = {f"{value:g}" for value, _ in pts}

    def clamp_quality() -> str:
        return "range_estimate" if sparse else "clamped"

    # بیرون از پوشش جدول
    if (direction == "higher_better" and raw_value < pts[0][0]) or (
        direction == "lower_better" and raw_value > pts[0][0]
    ):
        return {"percentile": 1.0 if not sparse else 5.0, "quality": clamp_quality()}
    if (direction == "higher_better" and raw_value > pts[-1][0]) or (
        direction == "lower_better" and raw_value < pts[-1][0]
    ):
        return {"percentile": 99.0 if not sparse else 95.0, "quality": clamp_quality()}

    # روی یک نقطه یا بین دو نقطه
    def finalize(pct: float) -> float:
        # نمره = درصدک «عملکرد»: برای lower_better (زمان/خطا)، درصدک توزیع خام وارون می‌شود
        return round(100.0 - pct, 1) if direction == "lower_better" else round(pct, 1)

    for index, (value, pct) in enumerate(pts):
        if raw_value == value and f"{value:g}" in exact_keys:
            return {
                "percentile": pct if direction == "higher_better" else 100.0 - pct,
                "quality": "exact" if not sparse else "range_estimate",
            }
        if index + 1 < len(pts):
            low_val, low_pct = pts[index]
            high_val, high_pct = pts[index + 1]
            lo, hi = (low_val, high_val) if low_val <= high_val else (high_val, low_val)
            if lo < raw_value < hi:
                ratio = (raw_value - low_val) / (high_val - low_val)
                pct = low_pct + ratio * (high_pct - low_pct)
                return {
                    "percentile": finalize(pct),
                    "quality": "interpolated" if not sparse else "range_estimate",
                }
    # مقدار دقیقاً برابر آخرین نقطه
    return {
        "percentile": finalize(pts[-1][1]),
        "quality": "exact" if not sparse else "range_estimate",
    }


def score_test(
    *,
    raw_value: float,
    norm: dict,
    direction: str = "higher_better",
) -> dict:
    """امتیاز یک آزمون در برابر ردیف نُرم + دلیل + نسخهٔ قاعده."""
    for field in ("test_key", "sex", "age_min", "age_max", "percentiles", "source"):
        if field not in norm:
            raise ApiError(f"ردیف نُرم فاقد {field} است", code="invalid_norm")
    estimate = estimate_percentile(
        raw_value=raw_value, percentiles=norm["percentiles"], direction=direction
    )
    return {
        "test_key": norm["test_key"],
        "raw_value": raw_value,
        "score": estimate["percentile"],  # نمره = درصدک (۰..۱۰۰)
        "quality": estimate["quality"],
        "reason": (
            f"{norm['test_key']} مقدار {raw_value} در برابر نُرم {norm['sex']}/{norm['age_min']}-{norm['age_max']} "
            f"← درصدک {estimate['percentile']} ({estimate['quality']}) — منبع: {norm['source'][:60]}"
        ),
        "rule_version": SCORE_VERSION,
    }


def is_real_change(
    *,
    old_value: float,
    new_value: float,
    sdc: float | None,
) -> dict:
    """گیت SDC: آیا تفاوت بازتست «واقعی» است یا نویز؟"""
    if old_value is None or new_value is None:
        raise ApiError("مقدار بازتست نامعلوم است — داده ناشناخته است نه صفر", code="invalid_raw")
    if sdc is None:
        return {
            "real_change": None,
            "delta": round(new_value - old_value, 4),
            "reason": "SDC برای این آزمون ثبت نشده — قضاوت «تغییر واقعی» نامعلوم (هرگز جعل نشود)",
            "rule_version": SCORE_VERSION,
        }
    if sdc <= 0:
        raise ApiError("SDC باید مثبت باشد", code="invalid_sdc")
    delta = round(new_value - old_value, 4)
    real = abs(delta) >= sdc
    return {
        "real_change": real,
        "delta": delta,
        "reason": (
            f"تغییر {delta} در برابر SDC={sdc} ← "
            + (
                "تغییر واقعی (فراتر از نویز بازتست)"
                if real
                else "در محدودهٔ نویز بازتست — بهبود/افت اعلام نشود"
            )
        ),
        "rule_version": SCORE_VERSION,
    }

"""قاعده‌های تنظیم خودکار بار (Autoregulation) — نسخهٔ `autoreg-1.0`.

قاعده‌های مربیگری (euristici) — نه معادلهٔ فیزیولوژیک (مشمول E07 نمی‌شوند).
منطق بر اساس «قانون ۲ برای ۲» و RPE (RIR) مستندسازی می‌شود.
"""

from __future__ import annotations

from app.errors import ApiError

AUTOREG_VERSION = "autoreg-1.0"

# افزایش بار وقتی وزنه‌زن بیش از هدف تکرار زده + RPE آسان (RIR ≥ 2)
STEP_UP_KG = 2.5
# کاهش بار وقتی تکرارها کمتر از هدف یا RPE سنگین (RIR = 0)
STEP_DOWN_KG = 5.0


def suggest_next_weight(
    *,
    last_weight: float,
    reps_done: int,
    target_reps: int,
    rpe: float | None = None,
) -> dict:
    """وزنهٔ پیشنهادی ست بعدی/هفتهٔ بعد + دلیل (زنجیرهٔ داده←قاعده←شاهد←تصمیم).

    - ورودی نامعتبر (منفی/صفر) → خطای صریح (هرگز صفر/نرمال جعل نشود).
    - خروجی همیشه شامل `reason` و `rule_version`.
    """
    if last_weight <= 0 or reps_done < 0 or target_reps <= 0:
        raise ApiError(
            "ورودی‌های نامعتبر (منفی/صفر) — داده ناشناخته است نه صفر", code="invalid_input"
        )
    if rpe is not None and not (1 <= rpe <= 10):
        raise ApiError("RPE باید بین ۱ و ۱۰ باشد", code="invalid_rpe")

    # قانون ۲ برای ۲: اگر ۲ تکرار بیشتر از هدف با RPE ≤ ۸ زده شد ← افزایش
    if reps_done >= target_reps + 2 and (rpe is None or rpe <= 8):
        return {
            "next_weight": round(last_weight + STEP_UP_KG, 1),
            "action": "increase",
            "reason": f"{reps_done} تکرار ≥ هدف+۲ با RPE={rpe} ← قانون ۲-برای-۲",
            "rule_version": AUTOREG_VERSION,
        }
    # تکرار کمتر از هدف یا RPE=۱۰ ← کاهش
    if reps_done < target_reps or (rpe is not None and rpe >= 10):
        return {
            "next_weight": max(round(last_weight - STEP_DOWN_KG, 1), 0.0),
            "action": "decrease",
            "reason": f"تکرار {reps_done}/{target_reps} یا RPE={rpe} ← محافظه‌کاری",
            "rule_version": AUTOREG_VERSION,
        }
    return {
        "next_weight": round(last_weight, 1),
        "action": "maintain",
        "reason": f"تکرار {reps_done}/{target_reps} در محدودهٔ هدف ← حفظ بار",
        "rule_version": AUTOREG_VERSION,
    }

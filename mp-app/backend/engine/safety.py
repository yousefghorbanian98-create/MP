"""پروتکل ایمنی سالمند سالم (D-016) — نسخهٔ قواعد safety-1.0.

وضعیت: PRD-gap (مرجع بازبینی حرفه‌ای مستقل نشده) — همانند gap_rules M05؛
اعداد «پیشنهاد طراحی»‌اند نه حکم بالینی تأییدشده (E13/E14).
"""

from __future__ import annotations

SENIOR_PROTOCOL_VERSION = "safety-1.0 (PRD-gap: مرجع بازبینی نشده)"

SENIOR_RULES: dict = {
    "population": "senior_healthy",
    "load_multiplier": 0.7,  # بار کمتر نسبت به بزرگسال
    "warmup_minutes_min": 10,
    "max_strength_testing": False,  # تست بیشینه ممنوع
    "balance_component_required": True,  # جزء تعادلی در هر جلسه
    "stop_criteria": [
        "درد قفسهٔ سینه/تنگی نفس غیرعادی",
        "سرگیجه/عدم‌تعادل",
        "درد مفاصل > 4 از 10 حین تمرین",
    ],
    "review_interval": "1 week",
    "source_note": "پیشنهاد مهندسی بر اساس consensus عمومی ایمنی سالمندی — نیازمند تأیید حرفه‌ای (E13)",
}


def apply_senior_protocol(plan: dict) -> dict:
    """اعمال قواعد ایمنی سالمند روی خروجی موتور — اعداد فقط از همین قواعد نسخه‌دار."""
    out = dict(plan)
    out["safety"] = SENIOR_RULES
    out["safety"]["version"] = SENIOR_PROTOCOL_VERSION
    if isinstance(out.get("days"), list):
        for day in out["days"]:
            for ex in day.get("exercises", []):
                if "weight" in ex and isinstance(ex["weight"], (int, float)):
                    ex["weight"] = round(ex["weight"] * SENIOR_RULES["load_multiplier"], 1)
    return out

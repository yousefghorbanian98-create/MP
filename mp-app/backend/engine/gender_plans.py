"""موتور پلن جنسیت‌محور — نسخهٔ `gender-plan-1.0` (M41-c2).

سیاست کسب‌وکار نسخه‌دار (تصمیم مالک باشگاه — نه ادعای علمی):
- پلن‌های آقایان/بانوان جدا: نام، قیمت و شرایط متفاوت (قابل پیکربندی در همین ماژول)
- «ماه بانوان = ۳۷ روز»: ۳۰ روز + ۷ روز جبران هفتهٔ قاعدگی (عدالت تمرینی)
  — قاعدهٔ محاسباتی ثابت و نسخه‌دار؛ هر خروجی reason + policy_version دارد.

هر عدد پیشنهادیِ قیمت در این ماژول «مقدار پیش‌فرض قابل تغییر مالک» است و
هیچ ادعای علمی/فروشی پشت آن ثبت نشده است.
"""

from __future__ import annotations

PLAN_POLICY_VERSION = "gender-plan-1.0"

BASE_MONTH_DAYS = 30
MENSTRUAL_RECOVERY_DAYS = 7  # جبران هفتهٔ قاعدگی — سیاست عدالت تمرینی (مالک)

# مقادیر قیمت = پیش‌فرض‌های قابل پیکربندی مالک (ریال) — نه ادعای بازار
PLANS: dict[str, dict[str, dict]] = {
    "monthly_basic": {
        "male": {"plan_name": "ماهانهٔ آقایان — پایه", "price_rial": 4_000_000},
        "female": {"plan_name": "ماهانهٔ بانوان — پایه", "price_rial": 3_600_000},
    },
    "monthly_plus": {
        "male": {"plan_name": "ماهانهٔ آقایان — پلاس", "price_rial": 6_500_000},
        "female": {"plan_name": "ماهانهٔ بانوان — پلاس", "price_rial": 5_800_000},
    },
    "quarterly": {
        "male": {"plan_name": "سه‌ماههٔ آقایان", "price_rial": 11_000_000},
        "female": {"plan_name": "سه‌ماههٔ بانوان", "price_rial": 10_200_000},
    },
}

WOMEN_MONTH_REASON = (
    "ماه بانوان ۳۷ روز = ۳۰ + ۷ روز جبران هفتهٔ قاعدگی (عدالت تمرینی) — "
    "سیاست کسب‌وکار نسخه‌دار (تصمیم مالک باشگاه، نه ادعای علمی)"
)
MEN_MONTH_REASON = "ماه آقایان ۳۰ روز — دورهٔ استاندارد اشتراک"


def women_month_days() -> int:
    """مدت ماه پلن بانوان — از قاعدهٔ ثابت محاسبه می‌شود، نه hardcode پراکنده."""
    return BASE_MONTH_DAYS + MENSTRUAL_RECOVERY_DAYS


def _duration_days(plan_key: str, gender: str) -> int:
    """هر «ماه» پلن بانوان = women_month_days (۳۷) — قاعدهٔ عمومی «ماه بانوان»."""
    months = {"monthly_basic": 1, "monthly_plus": 1, "quarterly": 3}[plan_key]
    month_len = women_month_days() if gender == "female" else BASE_MONTH_DAYS
    return months * month_len


def resolve_plan(*, plan_key: str, gender: str) -> dict:
    """پلن را بر اساس جنسیت حل می‌کند — نام/قیمت/مدت + reason + نسخهٔ سیاست."""
    if plan_key not in PLANS:
        raise KeyError(plan_key)
    if gender not in ("male", "female"):
        raise ValueError("جنسیت باید male یا female باشد (ثبت‌نام M41-c1 اجباری است)")
    spec = PLANS[plan_key][gender]
    duration = _duration_days(plan_key, gender)
    reason = WOMEN_MONTH_REASON if gender == "female" else MEN_MONTH_REASON
    return {
        "plan_key": plan_key,
        "gender": gender,
        "plan_name": spec["plan_name"],
        "price_rial": spec["price_rial"],
        "duration_days": duration,
        "reason": reason,
        "policy_version": PLAN_POLICY_VERSION,
    }


def list_plans() -> list[dict]:
    """فهرست همهٔ پلن‌ها برای هر دو جنسیت (نمایش ادمین/فروش)."""
    out = []
    for plan_key in PLANS:
        for gender in ("male", "female"):
            out.append(resolve_plan(plan_key=plan_key, gender=gender))
    return out

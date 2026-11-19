"""۱۳ محور + نگاشت رسمی ۱۴ دامنه ↔ ۱۳ محور + ماتریس پوشش بدون جمع دوبارهٔ بار (M24).

قاعدهٔ بسته: «جامع بودن = تمرین برابر همه نیست»؛ حرکت چندبرچسبی بارش فقط یک‌بار حساب می‌شود.
"""

from __future__ import annotations

# ۱۳ محور — دقیقاً مطابق CURRENT-SPEC بستهٔ fitness-handoff
AXES_13: list[dict[str, str]] = [
    {"id": "axis-01", "name_fa": "تعادل و پایداری"},
    {"id": "axis-02", "name_fa": "قدرت عملکردی"},
    {"id": "axis-03", "name_fa": "استقامت قلبی‌عروقی"},
    {"id": "axis-04", "name_fa": "استقامت عضلانی"},
    {"id": "axis-05", "name_fa": "تعادل عضلانی و وضعیت بدنی"},
    {"id": "axis-06", "name_fa": "پایداری مرکز بدن"},
    {"id": "axis-07", "name_fa": "هماهنگی و مهارت حرکتی"},
    {"id": "axis-08", "name_fa": "مکانیک بدن و مهارت بلند کردن بار"},
    {"id": "axis-09", "name_fa": "قدرت گرفتن و مهارت دست"},
    {"id": "axis-10", "name_fa": "تنفس و کنترل فشار"},
    {"id": "axis-11", "name_fa": "بازیابی، خواب و مدیریت بار"},
    {"id": "axis-12", "name_fa": "پیشگیری از آسیب و آگاهی از بدن"},
    {"id": "axis-13", "name_fa": "مهارت‌های پایه زندگی ورزشی"},
]

# نگاشت رسمی: دامنهٔ ارزیابی ۱..۱۴ (M05) ← محورها (یک دامنه می‌تواند چند محور را پوشش دهد)
# منطق: دامنه‌های سلامت/عملکردی/مهارتی/سبک زندگی M05 بر پایهٔ مدل «سلامت-عملکردی» PRD.
DOMAIN14_TO_AXES: dict[int, list[str]] = {
    1: ["axis-11"],  # سلامتی-۱: بازیابی/خواب
    2: ["axis-11", "axis-12"],  # سلامتی-۲: مدیریت بار/آگاهی بدن
    3: ["axis-12"],  # سلامتی-۳: پیشگیری آسیب
    4: ["axis-02"],  # عملکردی-۱: قدرت عملکردی
    5: ["axis-03"],  # عملکردی-۲: استقامت قلبی‌عروقی
    6: ["axis-04"],  # عملکردی-۳: استقامت عضلانی
    7: ["axis-01", "axis-06"],  # عملکردی-۴: تعادل/پایداری مرکز
    8: ["axis-05"],  # عملکردی-۵: تعادل عضلانی/وضعیت
    9: ["axis-06"],  # عملکردی-۶: پایداری مرکز بدن
    10: ["axis-07"],  # مهارتی-۱: هماهنگی
    11: ["axis-08"],  # مهارتی-۲: مکانیک بلند بار
    12: ["axis-09"],  # مهارتی-۳: قدرت گرفتن/مهارت دست
    13: ["axis-10"],  # مهارتی-۴: تنفس/کنترل فشار
    14: ["axis-13"],  # سبک زندگی: مهارت پایه زندگی ورزشی
}

# وضعیت‌های مجاز هر محور (پیشنهادی بسته — با دلیل اجباری)
AXIS_STATUSES = (
    "direct_training",
    "covered_in_other_task",
    "education_monitoring",
    "low_priority_now",
    "insufficient_data",
    "out_of_current_scope",
    "needs_review_referral",
)


def axes_for_domains(domain_scores: dict[int, float]) -> dict[str, dict]:
    """وضعیت هر محور از امتیازهای دامنه — نامعلوم هرگز صفر/طبیعی فرض نمی‌شود (E01)."""
    out: dict[str, dict] = {}
    for axis in AXES_13:
        src = [d for d, ax in DOMAIN14_TO_AXES.items() if axis["id"] in ax and d in domain_scores]
        if not src:
            out[axis["id"]] = {
                "name_fa": axis["name_fa"],
                "status": "insufficient_data",
                "reason": "دامنهٔ مرتبط ارزیابی نشده — نامعلوم، نه طبیعی (E01)",
            }
            continue
        score = sum(domain_scores[d] for d in src) / len(src)
        if score >= 4:
            status, reason = (
                "covered_in_other_task",
                f"امتیاز بالا ({score:.1f}/5) از دامنه‌های {src} — پوشش ضمنی",
            )
        elif score <= 1:
            status, reason = (
                "direct_training",
                f"امتیاز پایین ({score:.1f}/5) از دامنه‌های {src} — نیاز به تمرین مستقیم",
            )
        else:
            status, reason = (
                "education_monitoring",
                f"امتیاز متوسط ({score:.1f}/5) از دامنه‌های {src}",
            )
        out[axis["id"]] = {"name_fa": axis["name_fa"], "status": status, "reason": reason}
    return out

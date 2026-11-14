"""ورودی هدف‌محور/نیازمحور با سؤال تکمیلی پویا (تصمیم قطعی ۵ + §۴ بسته).

سؤال‌های تکمیلی هر مسیر با هدف و محدودیت فرد تغییر می‌کند — فرم ثابت نیست.
"""

from __future__ import annotations

# پایهٔ مشترک (تصمیم قطعی ۵)
BASE_QUESTIONS = [
    {"id": "age", "text": "سن شما چند است؟", "type": "number"},
    {"id": "experience", "text": "سابقهٔ تمرین و وقفهٔ اخیر", "type": "choice",
     "options": ["مبتدی", "متوسط", "پیشرفته", "بعد از وقفه"]},
    {"id": "weekly_days", "text": "چند روز در هفته واقعاً می‌توانید تمرین کنید؟", "type": "number"},
    {"id": "session_minutes", "text": "مدت واقعی هر جلسه (دقیقه، شامل استراحت)", "type": "number"},
    {"id": "equipment", "text": "تجهیزات در دسترس", "type": "multi",
     "options": ["هالتر", "دمبل", "دستگاه", "کش", "بدون تجهیزات"]},
    {"id": "off_gym_activity", "text": "فعالیت خارج از باشگاه (شغل/پیاده‌روی/...)", "type": "text"},
    {"id": "barriers", "text": "موانع پایبندی (خواب/زمان/استرس/...)", "type": "text"},
]

# سؤال‌های تکمیلی هدف‌محور
GOAL_FOLLOWUPS: dict[str, list[dict]] = {
    "hypertrophy": [
        {"id": "recent_volume", "text": "حجم تمرین اخیر (ست در هفته به ازای عضلات هدف)", "type": "text"},
        {"id": "volume_tolerance", "text": "تحمل حجم (خستگی بعد از جلسات سنگین؟)", "type": "choice",
         "options": ["کم", "متوسط", "زیاد"]},
        {"id": "priority_muscles", "text": "عضلات اولویت‌دار", "type": "multi",
         "options": ["سینه", "پشت", "شانه", "بازو", "پا", "شکم"]},
    ],
    "strength": [
        {"id": "target_lifts", "text": "حرکات هدف (مثلاً اسکوات/پرس)", "type": "text"},
        {"id": "recent_lifts", "text": "بار/تکرار اخیر حرکات هدف", "type": "text"},
        {"id": "technique_note", "text": "تکنیک مشاهده‌شده (مربی)", "type": "text"},
    ],
    "fat_loss": [
        {"id": "weight_trend", "text": "روند وزن ۳ ماه اخیر", "type": "choice",
         "options": ["افزایش", "ثابت", "کاهش"]},
        {"id": "nutrition_permission", "text": "اجازهٔ بررسی رفتارهای غذایی؟", "type": "bool"},
        {"id": "clinical_signs", "text": "نشانه‌های نیاز به متخصص (در صورت وجود)", "type": "text"},
    ],
    "endurance": [
        {"id": "cardio_history", "text": "سابقهٔ هوازی", "type": "text"},
        {"id": "effort_tolerance", "text": "تحمل تلاش", "type": "choice", "options": ["کم", "متوسط", "زیاد"]},
    ],
    "sport_performance": [
        {"id": "sport_position", "text": "رشته/پست", "type": "text"},
        {"id": "season_phase", "text": "فاز فصل", "type": "choice", "options": "پیش‌فصل|درفصل|پس‌فصل|انتقالی"},
        {"id": "match_calendar", "text": "تقویم مسابقه", "type": "text"},
    ],
    "daily_life": [
        {"id": "daily_tasks", "text": "تکالیف روزمرهٔ موردنیاز", "type": "text"},
        {"id": "fall_risk", "text": "سابقهٔ افتادن/عدم‌تعادل؟", "type": "bool"},
    ],
}

# وضعیت‌های خاص ← فقط دادهٔ مرتبط و مجاز (تصمیم قطعی — حداقل‌سازی)
SPECIAL_CONDITION_QUESTIONS = {
    "symptoms": {"id": "symptoms", "text": "علائم مرتبط با هدف (درد/تنگی نفس/...)", "type": "text"},
    "medication": {"id": "medication", "text": "داروهای مؤثر بر تمرین", "type": "text"},
    "professional_clearance": {"id": "clearance", "text": "مجوز/نظر متخصص در صورت وجود", "type": "text"},
}


def next_questions(goal: str, constraints: list[str] | None = None, answered_ids: list[str] | None = None) -> list[dict]:
    """سؤال بعدی بر اساس هدف + محدودیت‌ها — پویا، نه فرم ثابت."""
    answered = set(answered_ids or [])
    qs = [q for q in BASE_QUESTIONS if q["id"] not in answered]
    for q in GOAL_FOLLOWUPS.get(goal, []):
        if q["id"] not in answered:
            qs.append(q)
    # محدودیت/آسیب ← سؤال وضعیت خاص فقط در صورت مرتبط بودن (حداقل‌سازی)
    if constraints and any(c for c in constraints):
        for q in SPECIAL_CONDITION_QUESTIONS.values():
            if q["id"] not in answered:
                qs.append(q)
    return qs

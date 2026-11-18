# گزارش بازبینی کد M15 — هوش مصنوعی (code-reviewer)

**بازبین:** ایجنت code-reviewer | **تاریخ:** 2026-11-14 (بازبینی پس‌انداخت — backfill)

## دامنه
`engine/workout.py` + `engine/nutrition.py` (موتورهای قطعی)، `modules/ai_engine/` (سرویس/روتر/اسکیما)، `tests/unit/test_engine.py` + `tests/integration/test_ai_engine.py`.

## یافته‌ها
- ✅ **گیت G8:** تست‌های صریح — اعداد فقط از جدول قواعد؛ `llm_explanation` فقط متن؛ قطعیت (ورودی یکتا ← خروجی یکتا)
- ✅ ریاضی Mifflin-St Jeor با assertion دقیق
- ⚠️ الگوی `_staff.counter` قبل از def (درس LEDGER #7) — رفع شد

## حکم
**صفر Blocker** — ۱۳۵ تست سبز / ۸۹٪.

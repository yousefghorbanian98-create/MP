# گزارش بازبینی کد M12 — کش/کارایی (code-reviewer)

**بازبین:** ایجنت code-reviewer | **تاریخ:** 2026-11-14 (بازبینی پس‌انداخت — backfill)

## دامنه
`cache/store.py` (CacheBackend/InMemory/Valkey با fallback)، `cache/keys.py`، سیم‌کشی در `modules/membership/service.py`، `tests/unit/test_cache.py`، `testing/performance-budget.md`.

## یافته‌ها
- ✅ **گیت invalidation:** تست `test_stale_member_list_not_served_after_create` — بعد از هر نوشتن، کش قدیمی هرگز سرو نمی‌شود
- ✅ fallback درون‌حافظه‌ای بدون سرور Valkey (NFR-6)
- ⚠️ کش سراسری باید در فیکسچر کلاینت تست reset شود — رفع شد (ایزولاسیون تست‌ها)

## حکم
**صفر Blocker** — ۱۱۱ تست سبز.

# INV-03 — بازبینی منبعی crosswalk صفحات کادر

> **وضعیت:** `PARTIAL / NOT_ACCEPTED`. این یادداشت فقط crosswalk ایستا را با source همان SHA مقایسه می‌کند؛ نقش/مجوز runtime، تست محصول یا پذیرش صفحه را ثابت نمی‌کند.

## منشأ و بازتولیدپذیری

- هدف generator: commit جداشدهٔ `352781043ad2ba202d8b3b459df1ce7e3d914ef7` (`origin/main` هنگام تولید). tracked source در worktree تمیز بود؛ ابزارها untracked بودند و خروجی‌ها بعد از جمع‌آوری metadata نوشته شدند.
- ابزارها از `yousefghorbanian98-create/Chat2DB`، ref=`arena/c1fb460b-chat2db`، مسیر `docs/mp-inv-redo/` آمده‌اند. SHA-256 ابزارها: `inv02_member_crosswalk.py`=`6d9305ad60e0c0e1eaaf3eb864cfa0ea42aec2c9fc937082e5ddce0df40c7cf2`; `inv03_staff_crosswalk.py`=`d70ab9c8c3e2046ba3418ed50efc7bb4d6615e6602413878ffb5e9b9b79731b2`; `run-inv-redo.sh`=`5c05932a07e3ddb197953b7b1c77d614fff1da19074524966b300f6c4378faa2`. ابزارهای دریافت‌شده در worktree اصلی untracked مانده‌اند.
- پوشهٔ `2026-11-27` برچسب/مسیر مرجع evidence است، نه زمان‌سنج اجرای command. script زمان `started_at` را serialize نمی‌کند؛ mtime فایل‌های خام INV-03 برابر `2026-11-27T11:21:00.162397Z` است و تنها نشانگر زمان نوشتن خروجی است.
- hashهای `routes.json`، `roleNav.ts`، `navigation.ts` و `appStore.ts` در JSON خام با فایل‌های checkout حاضر تطبیق داده شدند. هیچ تست محصولی، build، browser/device یا CI در این بازبینی اجرا نشد.

## خروجی خام — بدون ویرایش

- [Markdown تولیدشده](staff-page-crosswalk.md) · SHA-256: `93ff6d1650d6ae74ac35dbd737a4f39eb47687979128800f28073aee14125dfc`
- [JSON تولیدشده](staff-page-crosswalk.json) · SHA-256: `3cd9cd2d8646542c66feab0e6f63b9012952468a2db63865e8426e0c7c8cf22c`
- شمارش اسکریپت: ۱۲ `PAGE_IDS`، ۱۲ route، ۱۴۱ مسیر API طبق loader، ۸ rule نقش parse‌شده، `PARTIAL_REVIEW=11` و `GAP=1`. این شمارش‌ها خروجی regex/static هستند، نه پوشش QA.

## یافته‌های منبعی

### ردیف `analytics`: GAP خام، call-site واقعی در source

Markdown/JSON خام برای `analytics` می‌گوید `apis_used=0` و `GAP`. در همان SHA:

- [Analytics.tsx](../../../mp-app/studio/src/pages/Analytics.tsx) توابع `fetchLeaderboards()` و `fetchChurnRisk()` را فراخوانی می‌کند.
- [adminApi.ts](../../../mp-app/studio/src/lib/adminApi.ts) این دو را به `${base}/admin/analytics/leaderboards` و `${base}/admin/analytics/churn-risk` وصل می‌کند.
- parser فقط `${API_BASE}/...` و شکل‌هایی از helper با آرگومان literal را می‌گیرد؛ `${base}/...` را نمی‌بیند. بنابراین دلیل «هیچ call-site وجود ندارد» برای این ردیف رد می‌شود. در عین حال، `tests=[]` در raw باقی است؛ نبود test-reference یا اجرای آن از این مرور حل نمی‌شود. هیچ status جدیدی برای ردیف صادر نمی‌کنیم و raw `GAP` را دست‌نخورده می‌گذاریم؛ این ردیف صرفاً call-site ایستا دارد و crosswalk کلی `PARTIAL/NOT_ACCEPTED` می‌ماند.

همین محدودیت روی بخشی از APIهای Settings نیز اثر دارد: [Settings.tsx](../../../mp-app/studio/src/pages/Settings.tsx) `AdminPermissions` و `RoleManager` را render می‌کند؛ این componentها از `adminApi.ts` استفاده می‌کنند، اما parser base-variable آن را نمی‌شناسد. بنابراین اعداد `apis_used`/فهرست consumer برای Settings را کامل تلقی نکنید.

### نقش‌ها: parser ناقص، UI rule معادل مجوز نیست

- در [roleNav.ts](../../../mp-app/studio/src/lib/roleNav.ts)، `ALL_STAFF` به‌صورت alias تعریف شده و شامل شش نقش موجود، از جمله `member` است؛ dashboard/chat/checkin/shop همین alias را استفاده می‌کنند. parser فقط آرایهٔ literal را می‌خواند و metadata تنها ۸ rule را parse کرده؛ `roles=[]` در آن چهار ردیف به معنی «بدون نقش» نیست.
- هم‌زمان، [App.tsx](../../../mp-app/studio/src/App.tsx) پیش از render صفحهٔ staff، `isStaffRole(role)` را بررسی می‌کند و `member` را رد می‌کند؛ `/member` هم به `MemberRoutePending` می‌رود. پس حتی ruleهای explicit در `roleNav.ts` که `member` را برای `programs`/`nutrition`/`assessment` فهرست می‌کنند، به‌تنهایی دسترسی مؤثر route را ثابت نمی‌کنند. این اختلاف باید در `SEC-01` با تصمیم/تست واقعی بررسی شود؛ در این یادداشت grant جدیدی استنتاج یا اعمال نمی‌شود.

## دامنه و نتیجه

- نقش‌های این crosswalk از UI `roleNav.ts` آمده‌اند؛ route contract، اجرای `rbac.py`، ownership، positive/negative role test، error/state behavior و browser/device review اثبات نشده‌اند.
- test-referenceهای گزارش‌شده فقط نام مسیر در فایل هستند؛ هیچ test در این بازبینی اجرا نشد. فایل‌های خام برای حفظ provenance تغییر داده نشده‌اند؛ این یادداشت false-negativeهای قطعی parser را جدا می‌کند.

`INV-03` حداکثر `PARTIAL / NOT_ACCEPTED` است و checkbox باز می‌ماند. `PWA-01=PROPOSED/NOT_RUN`؛ release `NO-GO`. پس از ثبت همین crosswalkها، گام مستقل بعدی `SEC-01` است؛ ماتریس نهایی باید شش نقش + ناشناس، route/action/data owner و deny-case سمت سرور را پوشش دهد.

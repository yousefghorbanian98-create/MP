# STAFF-01 (الف) — گیت کامل‌بودن نقشهٔ کارکنان (2026-11-27)

```text
STAFF-01/PWA-40=PARTIAL/NOT_ACCEPTED
GATE=tests/staffRouteMap.test.ts (4 تست) + tests/staffRouteMapBaseline.json (ratchet)
NEW_ENDPOINT=no · NEW_SOURCE=no (فقط گیت و baseline)
MUTATIONS_PROVEN=3
```

- منبع حقیقت: `PAGE_IDS` در `src/stores/appStore.ts:10-24` (۱۲ صفحه).
- برای هر صفحه سه چیز سنجیده می‌شود:
  1. **مسیر:** `parseStudioRoute("/staff/<page>")` همان صفحه را برمی‌گرداند.
  2. **رندر:** نقشهٔ `pages` در `src/App.tsx:46-59` دقیقاً کلیدهای `PAGE_IDS` را دارد و هر
     نام کامپوننت واقعاً با `import { Name } from "./pages/…"` وصل است.
  3. **تست اختصاصی:** دست‌کم یک فایل در `tests/` همان کامپوننت را import می‌کند.
- بدهی موجود پنهان نشده: `members` و `analytics` امروز تست اختصاصی ندارند و در
  `tests/staffRouteMapBaseline.json` ثبت شده‌اند. این فهرست ratchet است: صفحهٔ تازه بدون
  تست ⇒ ردیف تازه ⇒ قرمز؛ نوشتن تست برای بدهی قدیمی ⇒ باید baseline کوچک شود.
- mutation (سه، همه قرمز و بازگشت byte-identical):
  حذف `settings` از نقشهٔ pages · افزودن صفحهٔ `reports` به `PAGE_IDS` بدون سیم‌کشی ·
  بادکردن baseline با `settings`
  ([`mutation-proof.txt`](mutation-proof.txt)).

## هنوز نه (چرا PARTIAL)
- **گیت ownership سمت سرور** (ستون دوم STAFF-01) هنوز نوشته نشده؛ باید روی ماتریس موجود
  `SEC-01` سوار شود، نه یک ماتریس دوم. `STAFF01_OWNERSHIP_GATE=not-yet`.
- `STAFF01_COMPLETENESS_GATE=pass` فقط برای سه محور بالا (route/render/test) است؛
  «مجوز واقعی سرور» را اثبات نمی‌کند.

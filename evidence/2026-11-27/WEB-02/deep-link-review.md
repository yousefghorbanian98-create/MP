# WEB-02 / PWA-11 — URL و deep-link مرور جاری

- **هدف بررسی:** route، return-to پس از ورود، refresh session و تاریخچهٔ مرورگر در source/tests همین checkout.
- **SHA:** `3e49232d2118e8212a4d1ddea20fc982da5cd13a` (source زیر `mp-app/studio` با origin/main diff ندارد؛ Studio CI برای همین SHA موفق است).
- **نتیجهٔ محدود:** `PARTIAL / NOT_ACCEPTED`; checkbox canonical WEB-02 باز و `PWA-11` حداکثر `PARTIAL` باقی می‌ماند.

## شواهد

- `src/lib/navigation.ts` مسیرهای `/login`, `/member`, `/staff/:page`, و home نقش‌محور را parse می‌کند؛ مسیر ناشناخته fail closed می‌شود. `normalizeReturnTo` scheme-relative/external، backslash/control chars، query/hash و مسیر غیرشناخته را رد می‌کند. `postLoginPath` مقصد مجاز را براساس نقش بازبینی می‌کند و عضو را به صفحهٔ staff نمی‌فرستد.
- `src/App.tsx` route محافظت‌شده را تا restore نشست در `checking` نگه می‌دارد، برای unauthenticated مقصد را به login منتقل می‌کند و role/page را پیش از نمایش staff کنترل می‌کند. `AuthContext.tsx`، token/refresh session را با `/members/me` بررسی و role غیر Studio را رد می‌کند.
- آزمون هدفمند محلی از `mp-app/studio/` روی همین checkout: `npm test -- tests/navigation.test.tsx tests/authFlow.test.tsx tests/topbarTitles.test.tsx` ⇒ **۳ فایل و ۲۰ تست PASS** (Vitest 3.2.7، `jsdom`). موارد پوشش: route مستقیم/ناشناخته، returnTo خارجی و query-bearing، نقش/صفحهٔ مجاز، refresh-token پس از 401، عدم نمایش صفحهٔ ممنوع و back/forward شبیه‌سازی‌شده.
- `nginx.conf` دارای `try_files $uri $uri/ /index.html` برای SPA است و API exact/subtree را جدا از fallback نگه می‌دارد. این بررسی config است؛ Nginx binary در sandbox حاضر نبود و روی SHA جاری HTTP refresh اجرا نشد.
- PR #30، `mp-ci` run=`45998409658` روی SHA بالا: Studio install/lint/Vitest/Vite build موفق است. این job headless CI است، نه مرورگر واقعی.

## محدودیت‌ها / blocker

- Chromium/Chrome/Firefox و Playwright در sandbox موجود نیستند؛ browser direct navigation، reload/hydration، bookmark و back/forward واقعی اجرا نشدند. `jsdom` شبیه‌سازی مرورگر کامل نیست.
- `/member` هنوز `MemberRoutePending` است و shell/OTP/دادهٔ عضو در این card پیاده‌سازی یا پذیرفته نشده؛ آزمون member نیز فقط fail-closed/عدم ورود عضو به Studio را ثابت می‌کند.
- پاسخ backend/staging واقعی، link expiration در browser، device/OS و reviewer مستقل بررسی نشدند.

کد محصول تغییر نکرد. Browser/OS/device/reviewer=`BLOCKED/NOT_RUN`; WEB-02 و PWA-11 پذیرفته نیستند؛ `PWA-01=PROPOSED/NOT_RUN`, release=`NO-GO`.

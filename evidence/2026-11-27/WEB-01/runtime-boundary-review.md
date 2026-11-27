# WEB-01 / PWA-10 — مرور مرز runtime وب و Electron

- **ارزیابی:** static source/config review روی HEAD=`3e49232d2118e8212a4d1ddea20fc982da5cd13a`، 2026-11-27 UTC.
- **وضعیت کارت:** `PARTIAL / NOT_ACCEPTED`. checkbox canonical WEB-01 باز می‌ماند؛ این مرور runtime دسکتاپ/مرورگر یا تأیید release نیست.

## شواهد همین checkout

| مسیر | آنچه از source/config دیده می‌شود | حد شاهد |
|---|---|---|
| `mp-app/studio/index.html`, `src/main.tsx`, `src/App.tsx` | ورودی اصلی HTML یک `#root` دارد؛ `src/main.tsx` ReactDOM را به همین root وصل می‌کند. | Static wiring، اجرای PWA یا نصب‌پذیری را ثابت نمی‌کند. |
| `mp-app/studio/vite.config.ts` | build خروجی `dist` دارد و ورودی‌های متعدد `rollupOptions.input` تعریف نشده‌اند. بازپخش `./node_modules/.bin/vite build --outDir <tmp> --emptyOutDir` روی همین checkout با Vite `5.4.21` و `4046` module موفق شد؛ فهرست HTML خروجی فقط `index.html` بود. | Build و entrypoint count، browser runtime/PWA installability را ثابت نمی‌کنند. |
| `mp-app/studio/electron/main.cjs` | Electron `BrowserWindow` را با `contextIsolation: true` و `nodeIntegration: false` می‌سازد؛ dev از `VITE_DEV_SERVER_URL` و حالت دیگر از `../dist/index.html` استفاده می‌کند. | فایل main/preload اجرا یا installer/desktop build تولید نشده است. |
| `mp-app/studio/electron/preload.cjs` | bridge محدود `mpStudio.version` را expose می‌کند؛ دسترسی مستقیم Node برای renderer فعال نشده است. | فقط source inspection است، نه بررسی امنیتی مستقل Electron. |
| `mp-app/studio/package.json` | پروژه یک Vite/React package است و script به نام `electron` به `electron .` اشاره دارد؛ `electron` dependency در manifest وجود ندارد. در sandbox هم executable و `electron` module حاضر نبودند. | دستور Electron در این checkout قابل اجرا/اثبات نشد؛ خروجی بسته‌بندی یا پشتیبانی OS معلوم نیست. |
| `mp-app/studio/visual-concepts.html`, `src/visual-concepts/*` | یک صفحهٔ preview با `concept-root` و React root جداگانه دارد. این فایل ورودی در build inputs پیکربندی نشده و به‌عنوان design preview جدا از `index.html` شناخته شد. | منشأ/license/وضعیت نگه‌داری این preview در این مرور دوباره ارزیابی نشد؛ نباید آن را محصول یا runtime انتشار حساب کرد. |

## CI همان SHA

در PR #30، `mp-ci` pull_request run=`45998409658`, head همان SHA، job=`studio`/check-run=`140503545504` با `Install`, ESLint, Vitest, Vite build و audit همگی `success` شد. این CI مسیر Studio وب را روی runner لینوکسی build/test کرد؛ چون Electron در dependencyها/runner نیست، معادل اجرای Electron یا پشتیبانی Windows/macOS نیست.

## نتیجه و گام بستن

- مرز معماریِ قابل مشاهده این است: **Studio React/Vite یک renderer وب مشترک دارد؛ Electron wrapper همان renderer خروجی `dist/index.html` را بار می‌کند**. صفحهٔ `visual-concepts` یک preview جداست و در Vite production inputs فهرست نشده است.
- برای `WEB-01` هنوز Electron executable/dependency/package و اجرای واقعی در target OS تأیید نشده؛ browser PWA نیز در این مرور launch نشد و reviewer مستقل در دسترس نبود. بنابراین وضعیت فقط `PARTIAL / NOT_ACCEPTED` است.
- تا تصمیم/تأیید مالک دربارهٔ پشتیبانی runtime دسکتاپ و آزمون لازم، هیچ Electron packaging یا تغییر product source انجام نشد. Browser/OS/device/reviewer غایب `BLOCKED/NOT_RUN`; `PWA-01=PROPOSED/NOT_RUN`; release=`NO-GO` باقی می‌مانند.

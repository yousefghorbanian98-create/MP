# M67 — احراز هویت و نشست Studio

**تاریخ:** 2026-11-16 UTC
**شاخه:** `arena/4f336f66-mp` · **پایه:** `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
**وضعیت:** `PASS` برای scope احراز هویت Studio در این گزارش؛ M66/D10 Flutter مستقل است و همچنان `UNKNOWN` می‌ماند.

## دامنه و تغییرهای تأییدشده

- فرم ورود OTP در Studio به `POST /api/v1/auth/otp/request` و `/verify` متصل است؛ رقم‌های فارسی/عربی نرمال می‌شوند و ورودی دستی JWT در Analytics حذف شده است.
- `AuthProvider` پیش از نمایش صفحات محافظت‌شده، نشست را با `GET /api/v1/members/me` بازیابی می‌کند. نقش‌های staff مجاز صریح‌اند؛ حساب `member` رد و refresh آن revoke می‌شود. `AppContent` علاوه بر فیلتر منو، دسترسی مستقیم به صفحهٔ غیرمجاز را هم fail-closed می‌کند.
- `sessionFetch` برای 401 غیر-auth یک refresh تک‌درخواستی مشترک و یک retry دارد؛ 403 و endpointهای `/auth/*` باعث refresh نمی‌شوند. شکست refresh یا 401 پس از retry، نشست محلی را پاک و رویداد انقضا را منتشر می‌کند.
- خروج، access/refresh محلی را **هم‌زمان و پیش از انتظار شبکه** پاک می‌کند؛ سپس `POST /auth/logout` برای revoke سمت سرور فرستاده می‌شود. مسیرهای محافظت‌شدهٔ Studio از `sessionFetch` عبور می‌کنند. در سورس، `fetch` خام فقط برای OTP/refresh/logout، مانیفست update و `/health` دیده شد.
- قرارداد backend تقویت شد: access JWTهای جدید OTP، claim `sid` برابر hash ردیف refresh همان نشست دارند؛ authentication آن ردیف را active و unexpired بررسی می‌کند. Rotation، access قبلی را revoke می‌کند و logout نیز access/refresh همان نشست را رد می‌کند. migration لازم نبود؛ از جدول موجود `refresh_tokens` استفاده شد.

## بازتولید و اصلاح امنیتی

تست backend پیش از اصلاح، با اجرای واقعی `POST /auth/logout` روی SQLite موقت نشان داد refresh revoke می‌شود، اما access bearer همان نشست همچنان `GET /members/me` را با **200** می‌گذراند. این محدودیت با claim `sid` متصل به refresh row اصلاح شد.

پس از اصلاح، تست M67 ثابت می‌کند: access پیش از logout معتبر است؛ rotation، refresh قبلی و access قبلی را رد می‌کند؛ access/refresh جدید تا زمان logout کار می‌کنند؛ و پس از logout، refresh و access همان نشست هر دو **401** می‌گیرند. در بازبینی raceهای کلاینت نیز چهار شکست با تست جاری بازتولید شد: پاسخ دیررس refresh پس از logout درخواست محافظت‌شده را دوباره می‌فرستاد؛ پاسخ دیررس logout می‌توانست نشست ورود تازه را پاک کند؛ refresh ناموفقِ نشست قبلی می‌توانست tokenهای تازهٔ ذخیره‌شده در tab دیگر را پاک کند؛ و 401 دیررسِ retry می‌توانست tokenهای تازه را پاک کند. `sessionGeneration`، تطبیق refresh/access token جاری پیش از ذخیره/پاک‌سازی پاسخ و حذف پاک‌سازی دوم پس از await این raceها را بستند؛ هر چهار regression در `mp-app/studio/tests/session.test.ts` هستند. پیامک واقعی، دیتابیس production یا credential واقعی استفاده نشد.

## شواهد اجرایی جاری

- Studio هدفمندِ جاری: `tests/session.test.ts`, `tests/settingsRole.test.tsx`, `tests/roleNav.test.tsx`, `tests/shopPage.test.tsx` → **36 passed / 0 failed** در چهار فایل (شامل raceهای نشست و گیت نقش).
- Studio کاملِ جاری پس از تغییرهای M67/M70: **217 passed / 9 skipped**؛ 33 فایل (32 pass، یک فایل contract با 9 تست skipشدهٔ ازپیش‌موجود). `npm test -- --reporter=dot` با exit 0؛ چند هشدار React `act(...)` در تست‌های قدیمی Shop/Nutrition/Readiness باقی است و شکست تست نیست.
- Studio build/typecheck: `npm run build` با `tsc -b` و Vite موفق؛ Vite هشدار موجود دربارهٔ import پویا/ایستای `api.ts` داد، نه خطای build.
- Backend هدفمند: `tests/integration/test_api_contract.py`, `test_m67_studio_auth.py`, `test_m65_qr_security.py` → **24 passed / 0 failed**؛ شامل auth، logout و regression امنیت QR. سه warning از deprecation/pytest-asyncio configuration بودند، نه شکست.
- Ruff: `ruff check` و `ruff format --check` روی چهار فایل backend تغییرکرده موفق.
- `npm ci` موفق. `npm audit --omit=dev`: **0 vulnerability**. `npm audit` کامل: **4 یافته در dev toolchain (3 moderate، 1 high)** در زنجیره‌های Vitest/`@vitest/mocker` و Vite/esbuild؛ `npm audit fix --force` اجرا نشد چون ارتقای breaking عمده پیشنهاد می‌دهد.
- `npm run lint` قابل اجرا نیست: `eslint` و config آن در Studio تعریف/نصب نشده‌اند؛ این اسکریپت قبل از این کار هم در manifest وجود داشت.

## مرزها و باقی‌مانده‌ها

- **ذخیره‌سازی امن‌تر از XSS ادعا نمی‌شود:** access و refresh token طبق قرارداد فعلی در `localStorage` هستند، نه HttpOnly cookie؛ این کار XSS-proof نیست.
- برای سازگاری rollout، JWTهای legacy فاقد `sid` همچنان stateless هستند و تا پایان عمر کوتاه access خود (طبق تنظیم backend) می‌توانند معتبر بمانند. JWTهای جدید OTP به ردیف نشست متصل‌اند.
- ورود staff به حساب ازپیش‌مجاز نیاز دارد؛ backend برای شمارهٔ جدید نقش `member` می‌سازد و Studio عمداً آن را نمی‌پذیرد. تست OTP با `dev_code` محلی بود؛ ارسال SMS و provider واقعی آزموده نشد.
- single-flight بین درخواست‌های هم‌زمان در یک runtime جاوااسکریپت آزموده شد؛ پاسخ‌های دیررس با generation و tokenهای فعلی مقایسه می‌شوند تا نشست تازه overwrite/پاک نشود. دو interleaving از shared `localStorage` به‌صورت تستی شبیه‌سازی شدند؛ قفل single-flight مشترک یا E2E واقعی بین چند tab/browser پیاده‌سازی/اجرا نشده است.
- کل backend suite، Flutter suite/build، CI/workflow، production DB، دستگاه واقعی، release/deploy، push و commit اجرا نشدند.
- M66/D10 هنوز باید روی کد جاری با mirror حل‌شدهٔ کاربر یا CI اجرا شود؛ نبود executable محلی Flutter blocker پروژه نیست.

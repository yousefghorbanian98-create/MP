# M71 — گیت مصرف واقعی API برای Studio و Client

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **PASS محلی** — فقط بر اساس گیت و آزمون‌های فعلی Studio؛ نه CI، backend full-suite یا E2E دستگاه.

## تغییر

`mp-app/studio/tests/apiCoverage.test.ts` از تطبیق زیررشتهٔ متنی به استخراج call واقعی تغییر کرد:

- TypeScript/TSX با AST بررسی می‌شود؛ فراخوانی‌های `fetch`/`sessionFetch` و wrapperهای API و مسیرهای شاخه‌ای/قالبی شناسایی می‌شوند.
- Dart با tokenizer بررسی می‌شود؛ comment و متن داخل string به‌عنوان call شمرده نمی‌شوند.
- تطبیق route پارامترهای تعریف‌شده در backend را می‌پذیرد، اما پارامتر استخراج‌شده از client را wildcard یک segment ثابت نمی‌کند. به‌این‌ترتیب `/payments/{id}/receipt` دیگر به‌اشتباه `/payments/invoice/{member_id}` را پوشش نمی‌دهد.
- استثنا باید route فعلیِ `routes.json`، دلیل، و یا call واقعی داشته باشد یا `TODO` صریح/مصرف‌کنندهٔ بیرونیِ دارای file evidence. استثنای منقضی و ادعای external بدون شاهد فایل نیز fail می‌شود.
- ادعای قدیمی برای `/members/memberships/plans` اصلاح شد: اپ فقط تاریخچهٔ عضویت `/members/{member_id}/memberships` را می‌خواند؛ این دو route یکی نیستند.

## پوشش مشاهده‌شده

- `mp-app/backend/api/routes.json`: **114 مسیر**؛ همه یا call قابل‌شناسایی در Studio/mobile دارند یا در `ROUTE_EXCEPTIONS` مستند شده‌اند.
- **34 مسیر بدون call مستقیم در دو اپ** در exception map ثبت شد: 31 مورد `TODO`، و 3 مورد عملیاتی با شاهد فایل: `/metrics` (Prometheus)، `/health/ready` (health-check) و شارژ دستیِ staff-only کیف‌پول (`ACCESS-AUDIT-2026-11-15.md`). این‌ها به‌عنوان consumer داخل اپ معرفی نشده‌اند.
- testهای probe کامنت/string-only را uncovered نگه می‌دارند، call واقعی با پارامتر را می‌پذیرند، شاخهٔ شرطی در route را می‌شمارند و تطبیق اشتباه invoice/receipt را رد می‌کنند. این ادامهٔ S1 است و **D6 در M61 بازگشایی نشده است**.

## اجرای جاری

- `npm test -- tests/apiCoverage.test.ts --reporter=dot` → **1 file passed; 4 passed, 0 failed**.
- `npm test -- --reporter=dot` → **217 passed / 9 skipped**؛ 32 فایل pass، یک فایل با 9 تست skipشدهٔ ازپیش‌موجود.
- `npm run build` → موفق؛ `tsc -b` و Vite build هر دو موفق.
- هشدارهای غیرمسدودکننده: React `act(...)` در تست‌های قدیمی؛ Vite هشدار import پویا/ایستای `api.ts` در `Shop.tsx`.
- یک typecheck جداگانهٔ فایل تست به‌علت نبود `@types/node` در وابستگی‌های Studio اجرا نشد؛ Vitest فایل را transform و اجرا کرد. `npm run build` پیکربندی عادی پروژه را typecheck می‌کند و tests را در `tsconfig.json` شامل نمی‌کند.

## محدودیت و scope

`routes.json` فقط pathها را می‌دهد؛ این گیت تطابق HTTP verb، schema بدنه، پاسخ runtime، مجوز backend یا مصرف‌کنندهٔ بیرون از repo را اثبات نمی‌کند. فهرست استثناها فقط وضعیت معلوم در repo را ثبت می‌کند؛ `TODO`ها مصرف واقعی نیستند. Backend full-suite، Flutter، CI، production، E2E/device، پرداخت واقعی، release/deploy و push اجرا نشدند.

`npm ci` فقط lockfile موجود را نصب کرد و **4 advisory** گزارش داد (3 moderate، 1 high)؛ `npm audit fix` اجرا نشد و dependency/lockfile عمداً تغییر داده نشد.

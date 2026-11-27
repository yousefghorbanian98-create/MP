# PR #30 — CI status, SHA and failure triage

> **Interpretation:** این گزارش فقط checkهای GitHub PR را ثبت می‌کند؛ `PASS` شدن گیت محلی مستندات یا pytest محلی، جای نتیجهٔ CI روی SHA PR نیست.

- PR: [#30](https://github.com/yousefghorbanian98-create/MP/pull/30), draft, base=`main`, head branch=`arena/5e0f64cf-mp`.
- SHA زمان ایجاد و query: `6593cb4bc7f42c9ada4ca7e499fe60124bf00703`; برابر `gh pr view 30 --json headRefOid` و SHA هر دو Actions runهای پایین بود.
- `gh pr checks 30 --watch` پایان یافت با exit `1`: **۱۲ check یکتا، ۱۰ pass، ۲ fail، ۰ pending**. خلاصهٔ raw و metadata در [`pr-30-checks-6593cb4.txt`](pr-30-checks-6593cb4.txt) و [`pr-30-meta.json`](pr-30-meta.json) است.

| Workflow/run | SHA اجرا | نتیجهٔ jobها |
|---|---|---|
| `mp-ci`, run `45996116481` | `6593cb4bc7f42c9ada4ca7e499fe60124bf00703` | ۷ موفق؛ `secret-scan` ناموفق |
| `pwa00-doc-quality`, run `45996116290` | همان SHA | Super-Linter و Reviewdog موفق؛ `PWA-00 patch applies cleanly and matches source docs` ناموفق |
| push run `45996082112` | همان SHA | backend, live-contract, studio, client-flutter, Android format/debug, docs, e2e-api و markdownlint موفق؛ `secret-scan` ناموفق |

## علت‌های قابل مشاهده و حد بررسی

1. **`secret-scan`:** annotationهای GitHub پنج match از rule=`generic-api-key` در commit=`6593cb4bc7f4` دادند: `INV-02-v1/member-capability-crosswalk.json:11`; `INV-02/member-capability-crosswalk.json:12–13`; `INV-03/staff-page-crosswalk.json:12–13`. بررسی هر پنج سطر نشان داد هر مقدار همان digest ثبت‌شده در `meta.sources` است؛ قالب ۶۴-رقمی SHA-256 دارد و با فایل منبع متناظر در checkout تطبیق می‌کند. پس این پنج مورد fingerprintهای منبع‌اند، نه API credential. به‌جای استثنای عمومی، پنج fingerprint دقیق commit:path:rule:line در `.gitleaksignore` ثبت و در `scripts/test_retired_signing_scan.py` صریحاً assert شد. هیچ مقدار secret چاپ نشد و rule تضعیف نشد. دریافت log کامل Actions با `gh run view --log-failed` از results receiver با `EOF` شکست خورد؛ annotationها و verification محلی منشأ همین پنج مورد را مشخص کردند. Gitleaks CLI 8.30.1 در این sandbox نصب نشد چون دریافت release asset با خطای TLS/شبکه متوقف شد؛ تست scanner محلی `NOT_RUN` است و باید در اجرای CI تازه تأیید شود.
2. **PWA-00 patch:** annotation نشان داد شکست در `cmp`های مرحلهٔ `Check the filtered patch against its pinned base` رخ داده است؛ نه در `git apply --check`. بازتولید از base ثابت `c46e792657e361cd09799c896c47149b4a5c4d86` همان را ثابت کرد: patch apply و cmp ADR-006 موفق بودند، اما source contract و evidence هرکدام یک پاراگراف backlink جاری DOC-05 بیشتر از patch داشتند. هر دو سند در diff PR بودند؛ بنابراین اختلاف واقعی و قابل توضیح بود. artifact `PWA-00-DIFF.patch` از همان pinned base با بدنهٔ جاری این دو source doc دوباره تولید شد. اجرای کامل منطق workflow پس از اصلاح اکنون apply-check، هر سه `cmp` و registry validation را PASS می‌کند؛ transcript پالایش‌شده در [`pwa00-patch-repro.txt`](pwa00-patch-repro.txt) است. این تغییر فقط هم‌ترازی patch مستنداتی است و status محصول/PWA را تغییر نمی‌دهد.

## CI پس از اصلاح

- Fix commit: `3e49232d2118e8212a4d1ddea20fc982da5cd13a`, برابر remote branch و `headRefOid` PR #30 در زمان بررسی.
- `gh pr checks 30` روی همین head نهایی شد: **۱۲ pass، ۰ fail، ۰ pending**. خروجی پالایش‌شده و run/job URLs در [`pr-30-checks-3e49232.txt`](pr-30-checks-3e49232.txt) هستند.
- `mp-ci` pull_request run `45998409658` و push run `45998396424`، و `pwa00-doc-quality` run `45998409713` هر سه با head SHA دقیق بالا `completed/success` هستند. در PR rerun، `Verify exact signing exceptions with synthetic secrets` و `Scan full Git history (redacted metadata)` هر دو pass شدند؛ check پچ PWA-00 و سه validation مرحله هم pass شدند.

نتیجه فقط CI برای SHA=`3e49232...` را سبز می‌کند؛ draft PR #30 همچنان open و ادغام‌نشده است. این نتیجه PWA/product acceptance را ارتقا نمی‌دهد: browser/OS/device/reviewer غایب `BLOCKED/NOT_RUN`، `PWA-01=PROPOSED/NOT_RUN` و release=`NO-GO` می‌مانند.

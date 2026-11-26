# فهرست تفکیک‌شدهٔ در دسترس / نیازمند Codespace یا محیط بیرونی

**تاریخ مرجع:** ۲۰۲۶-۱۱-۲۳ UTC · **شاخه:** `arena/5e0f64cf-mp` · **HEAD:** `d92817f4151ebbafb25425b7b28776a4cc1180dc` · **پایه:** `35d4b35184b4148c658b415bd009fc076bf24e00`

> **دامنهٔ فهرست:** فقط سه مورد بازِ Motion که همین حلقه دنبال می‌کرد: `MK-PWA-01-FU-01`, `MK-PWA-02`, `O3-08`. این فهرست جایگزین backlog پنجاه‌تایی PWA، تأیید محصول، یا release Go/No-Go نیست؛ وضعیت canonical آن‌ها را تغییر نمی‌دهد. `AVAILABLE` یعنی در این sandbox امکان تولید شاهد بوده، نه این‌که کل محصول پذیرفته شده باشد.

## فهرست ۱ — اکنون در دسترس بود و انجام شد

| # | کار/گیت | نتیجهٔ قابل‌مشاهده | مرز ادعا |
|---|---|---|---|
| 1 | Crosswalk ایستای current-tree (`MK-PWA-01-FU-01`) | نگاشت source/hash/line/test برای helper، صفحات، اجزای مشترک، CSS/Tailwind و lab در [crosswalk](studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md) موجود است. | بازبینی source است؛ به‌تنهایی review مستقل یا پذیرش runtime نیست. |
| 2 | Unit/component + کیفیت Studio (`MK-PWA-02/05`) | اجرای تازه در همین worktree: `npm test -- --reporter=dot` → **۵۰ فایل PASS، ۲ SKIP؛ ۳۴۵ PASS، ۱۰ SKIP، صفر fail**؛ `npm run lint` exit 0؛ `npm run build` exit 0، TypeScript و Vite `5.4.21` با ۴۰۴۵ module. | JSDOM هشدار `getComputedStyle` و React `act(...)` داشت؛ skipها pass نیستند. این‌ها CI روی remote نیستند. |
| 3 | Browser synthetic روی VisualConcepts | Chromium headless: **۱۳/۱۳ گروه assertion PASS**؛ reduced computed style، delay/duration، stagger سقف‌دار، رفت‌وبرگشت زندهٔ preference، ورود/خروج، selection و حفظ DOM/focus/draft؛ `matchMedia` غایب هم fail-closed شد. | دادهٔ آزمایشگاهی و `emulateMedia`؛ نه تنظیم OS یا دستگاه هدف. |
| 4 | Browser synthetic روی route واقعی `Studio → CheckIn` | **۱۰/۱۰ گروه assertion PASS** با token/API fixture کاملاً ساختگی؛ tab-order محدود و Enter، خط اسکن ثابت در reduced/متحرک در normal، تغییر زندهٔ preference، حفظ focus/state، و fallback در نبود `matchMedia`. `pageerror` و درخواست غیرمحلی صفر. | فقط Vite dev server و route چک‌این؛ backend/auth واقعی، همهٔ routeها یا امنیت نشست سنجیده نشد. جزئیات در [crosswalk](studio-motion-current-tree-static-crosswalk-2026-11-23.fa.md). |
| 5 | Screenshot مصنوعی از route چک‌این در reduced | [بازکردن تصویر ۱۴۴۰×۱۰۰۰](../../../artifacts/motion-availability-qa-2026-11-23/studio-checkin-reduced.png)؛ SHA-256=`03ca06c83a9034eaeb7465da2b201a8c748fc82a56308dfce5fa03fb13e35f4b`. | تصویر با `Synthetic QA` و دادهٔ fixture است؛ یک viewport headless، نه گواهی visual QA چنددستگاهی. |
| 6 | GitHub read-only / CI baseline در برابر PR اسناد | PRهای #25/#26 و runهای قدیمی `mp-ci` روی `d92817f` موفق بودند. روی head مستنداتی `4deb148`، Docs CI در push/PR PASS و backend در هر دو FAIL شد (علت بازتولیدشده در پایین). | PR #27 فقط ۷ مسیر handoff/docs را دارد؛ هیچ‌کدام تغییرهای source/test dirty این worktree را نمی‌آزمایند. شکست backend از assertion شمارش Markdownِ منسوخ در تست است، نه از آستانهٔ پوشش؛ green baseline را به source dirty تعمیم ندهید. |
| 7 | Docs gate و ثبت شاهد | Workspace کامل: `python3 scripts/docs_gate.py` → **۲۲ Markdown، ۳۱۵ لینک محلی، ۱۲ Mermaid**؛ clean PR tree شبیه‌سازی‌شده با crosswalk اصلاح‌شده: **۲۲ Markdown، ۲۹۷ لینک محلی، ۱۲ Mermaid**؛ هر دو PASS، `git diff --check` exit 0. | شمار لینک‌ها به‌خاطر تفاوت local dirty docs / clean PR tree متفاوت است. پس از اصلاح لینک inventory تاریخی، Docs CI روی head `4deb148` PASS شد (push run `45811802201` و PR run `45811811391`). |


**ابزار مرورگر موقت:** Node `v22.22.3`، Vite `5.4.21`، Playwright Core `1.65.1`، `@sparticuz/chromium@158.0.0` با Chromium `153.0.8010.0`. harness و نصب موقت زیر `/tmp/arena-mp-motion-browser-tools` بودند و به manifest یا dependencyهای محصول اضافه نشدند.

## فهرست ۲ — اکنون در این sandbox در دسترس نیست / نیازمند شاهد بیرونی

| # | نیاز باز | چرا در اینجا بسته نشد | در Codespace چه می‌شود؟ |
|---|---|---|---|
| 1 | ترجیح واقعی OS و browser/device هدف | `prefers-reduced-motion` فقط با Playwright emulated شد؛ headless Linux، تلفن یا setting دستگاه واقعی نیست. | می‌توان build و browser headless را تکرار کرد؛ برای setting سیستم و لمس/تفاوت دستگاه، خودِ دستگاه/مرورگر کاربر لازم است. |
| 2 | بازبینی مستقل G9 | بازبینی همین عامل، مستقل محسوب نمی‌شود؛ reviewer دوم/تصمیم‌گیر بیرونی در ابزار حاضر نیست. | Codespace این را به‌تنهایی حل نمی‌کند؛ diff باید توسط reviewer مستقل بررسی و نتیجه‌اش ثبت شود. |
| 3 | Screen reader / AT و بررسی دستی کامل | در این نوبت screen-reader اجرا نشد؛ در PATH فعلی ابزارهای Orca/NVDA/VoiceOver در دسترس/قابل اجرا دیده نشدند. آزمون Tab/Enter محدود است و WCAG را اثبات نمی‌کند. | می‌توان تست‌های قابل‌اسکریپت را اجرا کرد؛ آزمون AT باید روی میزبان/دستگاه دارای screen reader انجام شود و لاگ/نتیجه ثبت شود. |
| 4 | CI برای source/test تغییرکردهٔ همین worktree | GitHub CI روی baseline `d92817f` سبز بوده، اما source فعلی dirty و بیرون از آن SHA است. PR #27 روی `4deb148` فقط اسناد را دارد؛ Docs CI سبز است، ولی source dirty را نمی‌آزماید. | پس از انتقال امن و allowlist دقیق تغییرهای source/test به همین branch و اجرای CI روی SHA همان commit، می‌توان این مورد را بازسنجی کرد. Codespace روی remote فعلی به‌تنهایی patchهای محلی را ندارد؛ backend fail در handoff head به‌علت test assertion منسوخ است و بررسی source dirty را انجام نمی‌دهد. |
| 5 | Merge نهایی این micro-loopها | PR #27 فقط مستندات/evidence handoff است و source/test dirty را شامل نمی‌شود؛ `MK-PWA-06` برای product loop هنوز به تکمیل مراحل، review و disposition نیاز دارد. | بعد از sync دقیق source، اجرای گیت‌های لازم و review مستقل می‌توان PR محدود کد ساخت؛ merge زودتر یا استفاده از PR اسناد به‌عنوان قبولی کد، gate را دور می‌زند. |
| 6 | پذیرش تمام صفحه‌ها/سفرها و گیت‌های عمومی PWA | browser smoke فقط VisualConcepts و یک route چک‌این را پوشش داد. install/offline/service-worker/update، backend، امنیت/حریم/مالی و release در scope این سه مورد نیستند. | فقط اگر parent مستقل فعال و contract داشته باشد؛ این‌ها را از روی screenshot یا synthetic fixture نبندید. |
| 7 | هدف دقیق دستگاه/browser و تصمیم پذیرش مالک | OQ-08 هدف کلی Android Chrome برای عضو و Chrome/Edge دسکتاپ برای کادر را می‌گوید؛ مدل/نسخهٔ دقیق و تأیید نهایی هنوز شاهد ندارند. مالکیت محصول به‌تنهایی جای reviewer مستقل را نمی‌گیرد (OQ-10). | مالک باید target/version و disposition محصولی را روشن کند؛ reviewer مستقل و آزمایشگر دستگاه باید جداگانه نتیجه بدهند. Codespace نمی‌تواند این تصمیم یا استقلال را بسازد. |

## بستهٔ یک‌جای Codespace و شرط انتقال

1. **اول SHA را روشن کنید:** source آزمایش‌شده از checkout با `HEAD=d92817f` بود؛ GitHub روی همان SHA دو CI سبز دارد، اما diffهای محلی و screenshot در آن CI نیستند. `origin/main` tree-identical به آن commit است (local ref فقط دو commit عقب‌تر بود). برای دیدن همان source در Codespace باید patch/allowlist دقیق روی **همین شاخه** انتقال یابد؛ `git add -A` نزنید. snapshot پیش از هر انتشار handoff، با `git status --porcelain=v1 -uall`: **۶۲ مسیر tracked تغییرکرده، ۲۶۳ مسیر untracked، stage صفر**؛ ۷۰ مسیر receipt خصوصی و ۱۹۳ مسیر دیگر (از جمله ۱۵۸ path زیر `artifacts/`). receiptها را باز/کپی/stage نکنید و `artifacts/` یا سایر درخت‌های untracked را به‌صورت والد وارد بسته نکنید.
2. روی همان SHA در Studio اجرا کنید: `npm ci`, سپس `npm test -- --reporter=dot`, `npm run lint`, `npm run build`. خروجی کامل، نسخه‌ها، SHA و شمار skip/fail را نگه دارید؛ چیزی را skip یا آستانه را کم نکنید.
3. Browser/OS را جداگانه ثبت کنید: نسخهٔ browser، OS/device، preference واقعی (نه فقط `emulateMedia`)، viewport، keyboard/focus، screenshot synthetic پالایش‌شده و خطا/درخواست شبکه. هرگز token یا دادهٔ عضو واقعی وارد fixture/screenshot نکنید.
4. یک reviewer مستقل، diff همان SHA و سه acceptance را بخواند و `PASS/FAIL/BLOCKED` با دلیل امضا/ثبت کند. Codespace به‌تنهایی reviewer یا دستگاه واقعی نیست.
5. پس از آن status و checklist را نرمال کنید؛ PR فقط از `arena/5e0f64cf-mp` و برای فایل‌های مجاز همان loop ساخته شود. `merge` فقط پس از review و گیت‌های لازم؛ تا آن زمان `PARTIAL` بماند.

## وضعیت و ایمنی مرج

- `MK-PWA-01-FU-01 = PARTIAL`, `MK-PWA-02 = PARTIAL`, `O3-08 = PARTIAL`: شواهد محلی/browser بهتر شدند، اما فهرست ۲ هنوز باز است.
- در زمان ثبت baseline، PRهای #25 و #26 ادغام شده بودند و هیچ PR باز برای این handoff وجود نداشت. محتوای شواهد از درخت dirty محلی است؛ هر انتشار اسناد/تصویر باید با allowlist جدا و بدون کد نامرتبط یا receipt انجام شود. انتشار handoff به‌تنهایی سه micro-loop را نمی‌بندد و مجوز merge محصولی/release نیست.
- پیش از هر merge بعدی، از stage کردن receiptهای `mp-app/backend/var/receipts/` یا سایر فایل‌های نامرتبط/private خودداری کنید. هیچ‌یک از ۵۰ parent canonical، release gate یا Go/No-Go تغییر نکرد.

## وضعیت PR handoff و CI — ادامهٔ همان مرز

- PR مستندات [#27](https://github.com/yousefghorbanian98-create/MP/pull/27) به `main` روی شاخهٔ جاری **OPEN** و محدود به ۷ مسیر allowlist‌شده است؛ روی head `4deb148fa22449abeae0c52ca76d3423d1a0b772`، GitHub آن را `BEHIND` گزارش کرد و `reviewDecision` خالی بود. PR هیچ source/test محصولی ندارد.
- روی head مستنداتی `4deb148`, push run `45811802201` و PR run `45811811391`: Documentation, Studio, client-flutter, pinned-SDK (از جمله Android debug compile و format), live-contract و secret-scan PASS؛ CodeRabbit PASS؛ `e2e-api` به‌خاطر `needs: [backend]` SKIPPED. در هر دو run، backend در `pytest + per-directory coverage gate` FAIL شد.
- Artifact diagnostics در API فهرست شد ولی `gh run download` با `EOF` شکست خورد. علت با بازتولید محلیِ command دقیق CI روی archive همان commit و Python 3.11.2 پیدا شد: **۱ failed، ۱۳۲۲ passed، ۲ skipped**؛ شکست `mp-app/backend/tests/integration/test_gate_codes.py::test_green_summary_counts_current_markdown_files_and_mermaid_blocks` است. آزمون هنوز انتظار دارد متن `20 Markdown files` باشد، اما docs gate روی tree فعلی **۲۲ Markdown** گزارش می‌کند. تمام آستانه‌های per-directory coverage PASS شدند (overall 91%); بنابراین علت، assertion مستندات قدیمی است، نه coverage threshold یا Motion runtime. artifact/log بیرونی همچنان بررسی‌نشده ماند.
- تستِ نیازمند اصلاح در `mp-app/backend/tests/integration/test_gate_codes.py:80` بیرون از allowlist هفت‌مسیرهٔ PR است؛ تا مجوز گسترش دامنه، هیچ تغییری در آن انجام نشد. **نه test skip شد، نه assertion/coverage threshold کاهش یافت.** برای سبزشدن backend باید اصلاح صریح و مجاز آن تست در scope قرار گیرد؛ source dirty Motion همچنان CI روی SHA دقیق ندارد.
- **نتیجهٔ اقدام:** PR #27 را merge نکن: backend red، PR پشت base است و reviewer decision ندارد. سه loop همچنان `PARTIAL`; handoff/docs نه پذیرش محصول است و نه بستن loop. هیچ check/skip/thresholdی دور زده یا پایین آورده نشده است.

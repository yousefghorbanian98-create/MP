# M108 — گیت‌های «فقط در Codespace» به CI منتقل شدند (SDK پین‌شده · format · کامپایل اندروید)

- تاریخ: ۲۰۲۶-۱۱-۱۸ · شاخه: `arena/4f336f66-mp` · محرک: پرسش کاربر — «می‌توانی خودت به‌جای من اینها را در کداسپیس انجام دهی؟»
- پاسخ کوتاه: **نه — ران کردنِ Codespace تو برایم ممکن نیست** ( credential این sandbox یک GitHub App token با scope مخزن است: `gh api /user/codespaces` → `0`، `X-OAuth-Scopes` خالی، پس `gh codespace ssh` هم نه). **اما بیشتر آن کارها را می‌شد از «دست‌انجام‌دادنیِ انسانی» درآورد و به گیت تبدیل کرد** — که انجام شد.

## ۱) آنچه اضافه شد

| تغییر | چرا |
|---|---|
| job جدید `client-pinned` در `ci.yml` | سه گیتی که یا وجود نداشتند یا فقط روی SDK شناور اجرا می‌شدند |
| «Verify the pin matches the devcontainer» | CI و Codespace باید **همان** Flutter را بسنجند؛ نسخه/revision از `.devcontainer/Dockerfile` پارس می‌شود تا drift بی‌صدا ممکن نباشد |
| `flutter test --coverage` + شمارش از `ci_test_failures.py --summary` | درصد coverage کلاینت تا پیش از این هیچ‌جا محاسبه نمی‌شد؛ شمارشِ `passed/failed/skipped` هم لازم بود چون «جاب سبز» تفاوت «probe اجرا شد / skip شد» را نشان نمی‌دهد |
| `flutter build apk --debug` | **همان گاهی که M87 را از ابتدا `UNKNOWN` نگه داشته بود**: کامپایل Kotlin/Gradle هیچ‌وقت روی این منبع اجرا نشده بود. `--debug` است و **هیچ keystore‌ای لمس نمی‌کند** (SEC-01 باز است؛ `apk.yml` هم trigger نشد) |
| `dart format --output=none --set-exit-if-changed` | گیت نبود؛ حالا هست، ولی فعلاً **غیربلاکینگ** (پایین‌تر: چرا) |
| annotation شاهد | عددها از API خوانده می‌شوند، نه فقط از لاگی که باید دستی باز شود |

## ۲) شواهد

| گیت | نتیجه |
|---|---|
| `client-pinned` روی `0b852d5` (run `44322049209`) | **pin check ✓** (CI Flutter = `3.50.0` / `ab2912035e160d9cad6306df307576da6128ebdb`، دقیقاً پینِ devcontainer) · `pub get` ✓ · **`dart format` ✗** → و چون *پیش از* بقیه چیده شده بود، `analyze`/`test`/apk **skip** شدند |
| درس همان run | یک گیتِ تازه نباید شاهدِ همسایه‌هایش را بخورد. بازچینش شد: `analyze` → `test+coverage` → `apk build` → format audit (غیربلاکینگ، با `|| echo`؛ `bash -e` CI است) — commit `2ac6ecc` |
| `client-pinned` روی `2ac6ecc` (run `44323120295`) | **✓ سبز، همهٔ گام‌ها**. annotation: «Flutter tests: **156 passed, 0 failed, 0 skipped** · coverage **77.2%** (3195/4140 lines) · debug apk **151 MB** · dart format: **65 file(s) still unformatted (advisory)**» |
| بقیهٔ jobها روی همین sha | `client-flutter` ✓ · `backend` ✓ · `studio` ✓ · `live-contract` ✓ · `docs` ✓ — تنها `secret-scan` ✗ (بدون تغییر، SEC-01) |

**چرا «0 skipped» مهم است:** probe سطح messengerِ M98 عمداً طوری نوشته شده که اگر SDK پیامی نفرستد `markTestSkipped` کند. «0 skipped» یعنی آن probe **واقعاً اجرا شد** و سه فراخوانی را دید — نه اینکه سبزی‌اش از نبودِ آزمون آمده باشد.

**و یک ادعای قبلی که اصلاح می‌شود:** در `runbooks/codespaces-execution.md` نوشته بودم `pip-audit` «هرگز اجرا نشده». **نادرست بود**: job `backend` آن را اجرا می‌کند و **بلاکینگ** است (`bandit -r . -ll -q` و `pip-audit` بدون `\|\| true`؛ فقط collectorِ دیباگ `|| true` دارد). سبز بودن آن job یعنی: روی محیطِ ساخته‌شده از `pyproject.toml`، هیچ CVE شناخته‌شده‌ای در نسخه‌های resolve‌شدهٔ امروز نیست. محدودیت واقعی‌اش این است که **lock در مخزن نیست**، پس «امروز» با «دیروز» می‌تواند فرق کند — آن را در ردیف تصمیمات نگه می‌دارم، نه به‌عنوان کارِ تو.

## ۳) حالا چه وضعیتی عوض شد

| Loop | قبل | بعد |
|---|---|---|
| **M87 Android outbox** | `UNKNOWN` (Kotlin/Gradle هرگز کامپایل نشده بود) | **`UNKNOWN → PASS (compile)`** — کامپایل `MainActivity.kt` و `OfflineFeedbackDatabase.kt` روی `2ac6ecc` سبز. persistence/restart و سیاست encryption **هنوز `UNKNOWN`** (فقط با گوشی؛ مرحلهٔ ۶) |
| M90 / M98 (و M66، M72–M84) | `PASS (client CI)` روی stable شناور | همان `PASS`، حالا **روی SDK پین‌شدهٔ ۳٫۵۰٫۰** هم تأییدشده، با شمارش ۱۵۶/۰/۰ |
| بدهیِ فرمت Client | نامعلوم | **۶۵ فایل unformatted** — اندازه‌گیری‌شده و ثبت‌شده؛ تبدیلش به گیتِ کشنده در **M109** انجام می‌شود، نه قبل از پرداخت |
| coverage Client | هیچ‌گاه سنجیده نشده | **۷۷٫۲٪** (۳۱۹۵/۴۱۴۰ خط) · بدون آستانه؛ آستانه‌گذاری بعد از پرداخت بدهیِ فرمت منطقی‌تر است |

## ۴) چه چیزی **هنوز** فقط با توست

1. **M109 (یک دستور، ۳۰ ثانیه):** پرداخت بدهیِ فرمت تا گیت بتواند کشنده شود — در همان Codespace:
   ```bash
   cd "$(git rev-parse --show-toplevel)/mp-app/client" && dart format lib test tools | tail -3
   git -C "$(git rev-parse --show-toplevel)" status --porcelain | head
   ```
   اگر راضی هستی، `git add -A mp-app/client && git commit -m "style: dart format (M109)" && git push origin HEAD:arena/4f336f66-mp` — من بعدش `|| echo` را برمی‌دارم و گیت را کشنده می‌کنم.
2. **مرحلهٔ ۶ runbook (گوشی):** cold/warm `am start -W` (M104)، `animator_duration_scale 0` (reduced-motion)، حس سه پالس، شیت رسید روی RTL، ماسک لانچر (M105/M106)، صف آفلاین روی restart (M87)، QR فیزیکی (M89). اینها را نه من می‌توانم بزنم نه CI؛ فیزیک است.
3. **تصمیم‌های باز:** SEC-01 (چرخش کلید → همین `secret-scan` را سبز می‌کند)، face-vs-QR، معیار بالینی M85، merchant درگاه، سیاست storage/consent برای M93–M96.

## ۵) محدودیت‌های همین loop

- `flutter build apk --debug` در CI **کامپایل** است؛ یعنی «APK ساخته می‌شود و AndroidManifest/ساختار lintVital را می‌شکند نه» — رفتار زمان اجرا روی دستگاه را اثبات نمی‌کند.
- size 151MB برای APK دیباگِ universal طبیعی است (همهٔ ABIها + بدون minify/strip)؛ **نباید** به‌عنوان «سایز اپ» گزارش شود. اگر بخواهی، بیلد `--split-per-abi` یا number سنجیده‌شدهٔ release را جدا می‌گیریم (که آن هم تا SEC-01 release واقعی نیست).
- عدد coverage کلاینت **کل `lib/`** است (۷۷٫۲٪) — کیفیت تست‌ها را نشان می‌دهد، نه درستی رفتار روی دستگاه؛ و آستانه ندارد، پس سبزِ آن تعهدی ایجاد نمی‌کند.
- «۰ skip» برای همین run صادق است؛ اگر روزی runner عوض شود و probe skip کند، همان عدد در annotation ما را می‌گوید (طراحیِ گیت هم همین بود).
- ECC/REA اجرا نشد؛ هیچ subagent ساختگی نیست. چک‌لیست‌های `.claude/agents/*` دستی اعمال شدند.

## ۶) بازگشت

`client-pinned` یک job اضافه است و هیچ گیت موجودی را عوض نکرده: حذف همان بلوک از `ci.yml`، برمی‌گرداند همه‌چیز را. `dart format` gate هم چون بلاک نمی‌کند، کد را دست نزده — **هیچ فایل Dart در این loop فرمت نشد** (گام format فقط با `--output=none` اجرا می‌شود؛ چیزی نوشتن ندارد).

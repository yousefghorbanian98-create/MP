# اجرای گیت‌های بیرون از agent sandbox — Codespace و دستگاه (M107)

> این فایل **دستور کار مرحله‌به‌مرحله** است، نه توضیح. هر مرحله یک خروجی دارد که باید عیناً فرستاده شود؛
> طبق قانون FINN، «اجرا نشدن» و «اجرای ناقص» هیچ‌کدام `PASS` نیستند و من (عامل داخل sandbox) تا دیدن
> همان خروجی وضعیت loop را عوض نمی‌کنم.
>
> ## 🔻 به‌روزرسانی ۲۰۲۶-۱۱-۱۸ (M108): بیشتر این مراحل به CI منتقل شد — اول آن را بخوان
>
> از جاب `client-pinned` (run `44323120295`، sha `2ac6ecc`) اینها **دیگر دستی خواسته نمی‌شوند**،
> چون CI هر push را با همان Flutter پین‌شدهٔ devcontainer (`3.50.0` / `ab2912035e16…`) می‌سنجد:
>
> | مرحلهٔ پایین | حالا در CI | شاهد جاری |
> |---|---|---|
> | ۲ (analyze/test/pinned) | ✓ `client-pinned` | 156 passed / 0 failed / **0 skipped** روی SDK پین‌شده |
> | ۲ (coverage) | ✓ `flutter test --coverage` | 77.2% (3195/4140 خط از `lib/`) |
> | ۳ (backend: pytest/ruff/bandit/**pip-audit**) | ✓ job `backend` — **از قبل**؛ `pip-audit` آن‌جا بلاکینگ است | سبز ⇒ هیچ CVE شناخته‌شده‌ای در نسخه‌های resolve‌شدهٔ امروز نیست (lock در مخزن نیست؛ این تنها محدودیتش) |
> | ۵ (`flutter build apk --debug`) | ✓ `client-pinned` | کامپایل Kotlin/Gradle سبز ⇒ بُعد compile در M87 از `UNKNOWN` درآمد |
> | ۲ (format) | ✓ گیت **کشنده** از M109 (PR #1) | ۶۵ فایل unformatted → ۰؛ `dart format --set-exit-if-changed` حالا CI را می‌شکند |
>
> **با تو فقط یک چیز می‌ماند:** مرحلهٔ ۶ و ۷ — گوشی واقعی، چون Codespace نه USB دارد نه KVM.
> بدهیِ فرمت (M109) هم در CI پرداخت شد، نه روی دوش تو: `finn/reports/m109-dart-format.md`. بقیهٔ مراحل را همچنان می‌توانی برای
> بازتولید محلی اجرا کنی، ولی **شاهدِ لازم نیستند**؛ لاگشان را برای «تأیید» می‌فرست اگر خواستی.
>
> فهرست چیزهایی که در agent sandbox نشد: `flutter analyze`/`flutter test`/build (SDK نیست)، Android SDK/Gradle،
> emulator/دستگاه، ماسک لانچر، و اندازه‌گیری startup. Codespace و CI سه تای اول را حل کردند؛
> دو تای آخر **روی لپ‌تاپ با گوشی** انجام می‌شود، نه در مرورگر.

## ۰) قوانین ثبت (پیش از هر دستور)

| قاعده | چرا |
|---|---|
| برای هر مرحله: نسخهٔ ابزار، **خروجی کامل**، و `echo "exit=$?"` را کپی کن | بدون exit code، «بدون خطا» یعنی «خوانده نشد» |
| لاگ را در یک فایل کنار بگذار: `tee /tmp/m107/step2-client.txt` | بعداً فقط همین فایل شاهد است، نه حافظهٔ گفتگو |
| `pubspec.lock`، `.dart_tool/`، `build/`، `.gradle/`، `local.properties` را commit نکن | gen‌شده‌اند؛ lockfile باید جدا بازبینی شود (regression R-014). در CI هم همین: `git add -A` بعد از `flutter pub get`/`test --coverage` این‌ها را داخل commit «فقط فرمت» می‌کشد (M109) |
| اثباتِ «تغییر مکانیکی» روی **چیزی که stage شده** باشد، نه کل درخت | گام‌های بعدی (pub get، analyze، test) خودشان فایل می‌سازند؛ اگر proof پیش از آن‌ها اجرا شود، چیزی را تأیید می‌کند که commit نخواهد شد |
| هیچ‌جا keystore، `key.properties`، token، یا secret واقعی بازسازی/append نکن | SEC-01 مسئلهٔ چرخش کلید است، نه نبود فایل |
| اگر مرحله‌ای شکست، **همان‌جا بایست** و لاگ را بفرست | زنجیره‌کردن مراحل روی پایهٔ شکسته، شاهد جعل می‌کند |

## ۱) ساخت Codespace (روی همین شاخه، نه `main`)

```bash
# از CLI (اختیاری؛ وب UI هم همان کار را می‌کند)
gh codespace create \
  --repo yousefghorbanian98-create/MP \
  --ref arena/4f336f66-mp \
  --retention 1 \
  --idle-timeout 30
gh codespace ls
gh codespace ssh -C <CODESPACE_NAME>       # ترمینال
```

- `--retention 1` روز یعنی بعد از حذف، ماشین نگه داشته نمی‌شود؛ `--idle-timeout 30` دقیقه برای توقف خودکار.
- build اولین بار ۲–۵ دقیقه طول می‌کشد (تصویر `ubuntu24.04` + آرشیو Flutter با SHA-256 پین‌شده؛ `post-create.sh`
  نسخهٔ framework را بررسی می‌کند و اگر نخورد، **build را می‌شکند**).
- **تأیید مبدأ، پیش از هر کاری:**

```bash
mkdir -p /tmp/m107 && tee /tmp/m107/step0-baseline.txt <<EOF
branch=$(git rev-parse --abbrev-ref HEAD)
sha=$(git rev-parse HEAD)
EOF
git status --porcelain | head          # باید پاک باشد (مگر چیزی عمداً ساخته باشی)
flutter --version --machine | tee /tmp/m107/step0-flutter.json
dart --version 2>&1 | tee -a /tmp/m107/step0-baseline.txt
java -version 2>&1 | tee -a /tmp/m107/step0-baseline.txt
```

`sha` باید با head نهاییِ `origin/arena/4f336f66-mp` برابر باشد؛ اگر نبود، `git fetch && git switch <branch> && git pull --ff-only`.

## ۲) گیت‌های Client (Flutter روی SDK پین‌شده)

CI اینها را روی `stable` **شناور** سبز کرده؛ ارزش Codespace این است که روی **۳٫۵۰٫۰ پین‌شده** و با
لاگ کامل، یک‌بار دیگر و مستقل اجرا شوند (و اگر فرق کردند، همان فرق، یافته است).

```bash
cd "$(git rev-parse --show-toplevel)/mp-app/client"

flutter pub get 2>&1 | tee /tmp/m107/step2-pubget.txt; echo "exit=$?"

# گیت اصلی — همان چیزی که در sandbox نشد
flutter analyze --no-fatal-infos 2>&1 | tee /tmp/m107/step2-analyze.txt; echo "exit=$?"
flutter test 2>&1 | tee /tmp/m107/step2-test.txt; echo "exit=$?"

# coverage (در CI نیست) — برای اینکه بدانیم تست‌ها چه چیزی را می‌پوشانند
flutter test --coverage 2>&1 | tail -5 | tee /tmp/m107/step2-coverage.txt
lcov --summary coverage/lcov.info 2>&1 | tee -a /tmp/m107/step2-coverage.txt || true

# گیت‌های ابزارِ مخزن
python3 tools/dart_gate.py --include-tests 2>&1 | tail -3 | tee /tmp/m107/step2-dartgate.txt
python3 tools/manifest_gate.py 2>&1 | tail -2 | tee -a /tmp/m107/step2-dartgate.txt
```

| شاهد مورد انتظار | چه چیزی را قفل/تأیید می‌کند |
|---|---|
| `analyze` بدون error/warning | M66 (D10 refresh)، M72–M84، **M90**، **M98** روی SDK پین‌شده |
| `flutter test` با صفر شکست و **بدون skip** | همان loopها + probe سطح messengerِ M98 (`test/motion_haptics_test.dart`) |
| `dart_gate` ۷۲ فایل / ۰ یافته | سازگاری گیت ایستا با analyzer واقعی (ادعای جایگزینی ندارد) |

## ۲-الف) M109 — بسته شد در CI؛ چیزی از تو خواسته نشد

بدهیِ فرمت را workflow `client-format-fix` پرداخت (PR #1، commit `d9a5bdc`): `dart format lib test tools`
روی همان SDK پین‌شده اجرا شد، سپس اثباتِ «فقط چیدمان» روی **blobهای staged** — ۶۶ فایل، همه `M`،
۱ فقط whitespace و ۶۵ با جابه‌جایی کامای انتهایی، **۰** تغییر معنایی — به‌علاوهٔ idempotency
(اجرای دوم بی‌تغییر) و `flutter analyze` + `flutter test --coverage` سبز روی درخت فرمت‌شده.
بعد از merge، گیتِ `dart format` در `client-pinned` `|| echo` را از دست داد و **کشنده** شد:
یک فایلِ فرمت‌نشده از این به بعد CI را می‌شکند، نه اینکه عددش در annotation بخوابد.

سه چیزی که همین‌جا یاد گرفتیم و به کار تو هم می‌آید:

| # | نکته | چرا |
|---|---|---|
| ۱ | بعد از `flutter pub get` / `flutter test --coverage` هرگز `git add -A` نکن | `pubspec.lock`، `coverage/lcov.info` و بلوک `analyzer: exclude:` که **خودِ flutter** در `analysis_options.yaml` تزریق می‌کند، کنار فرمت stage می‌شوند — یک commit مکانیکی از آن لحظه مکانیکی نیست. `git add -u -- '*.dart'` همان چیزی است که می‌خواهی |
| ۲ | «diff فقط whitespace است» تنهایش کافی نیست | formatterِ tall-style کامای انتهایی را وقتی فهرست را می‌شکند جابه‌جا می‌کند؛ مقایسه باید با حذف کاماها هم بشود و **جدا شمرده** شود، وگرنه ۶۵ فایلِ سالم رد می‌شوند (این دقیقاً اولین اجرای ما را فیل کرد) |
| ۳ | بازتولید: `gh workflow run client-format-fix.yml` | dispatch-only است و اگر بدهی صفر باشد هیچ PR نمی‌سازد (`NO_CHANGES=1`) — اجرای مجدد بی‌ضرر است |
| ۴ | `dart format` را **همیشه بعد از** `flutter pub get` بزن | formatter نسخهٔ زبانی را از `package_config.json` می‌خواند؛ بی‌`pub get` به tall style فرمت می‌کند و با آن، برای `sdk: ">=3.3.0"` این مخزن، به short style. هر دو «درست»اند ولی فقط دومی را گیت می‌پذیرد — و همین تله، PR #1 را یک روز بعد ۵۳ فایلِ «unformatted» کرد |
| ۵ | بعد از یک reformat بزرگ، ٪coverage را با عددِ قبلی مقایسه نکن | `lcov` خط‌به‌خط می‌شمارد؛ فرمت، تعداد خطوطِ قابل‌سنجش را عوض می‌کند (این‌جا ۴۱۴۰ → ۴۴۲۶ خط و ۷۷٫۲٪ → ۷۶٫۷٪، بدون آنکه تستی کم یا زیاد شده باشد). مقایسهٔ درست، تعداد تست‌ها و خطوطِ از‌دست‌رفته است |
| ۶ | در `permissions:` کلید `metadata:` ننویس | «`metadata: read`» در مستندات GITHUB_TOKEN توصیه‌شده به‌نظر می‌رسد، ولی کلیدِ مجازِ `permissions` نیست: GitHub با آن **کل فایل** را رد می‌کند («failed to parse workflow: Unexpected value 'metadata'»، run `44349667465`، صفر job) |

> تزریق `analysis_options.yaml` یک تصمیمِ باز است، نه کارِ تو: اگر آن exclusion commit نشود،
> هر `flutter pub get` دوباره بازنویسی‌اش می‌کند. فعلاً commit نشده تا این PR فقط فرمت بماند.

## ۳) گیت‌های بک‌اند (اختیاری — CI اینها را می‌سنجد)

```bash
REPO="$(git rev-parse --show-toplevel)"
mkdir -p /tmp/m107/backup /tmp/m107/extras
cd "$REPO"
# venv **پاک** و فقط از pyproject — همان معنایی که job بک‌اند CI دارد
python3 -m venv /tmp/m107/venv && /tmp/m107/venv/bin/pip install -q -e "mp-app/backend[dev]" pip-audit
V=/tmp/m107/venv/bin/python

cd "$REPO/mp-app/backend"
$V -m pytest -q tests 2>&1 | tail -5 | tee /tmp/m107/step3-pytest.txt   # انتظار: 872 passed / 1 skipped
$V -m ruff check . 2>&1 | tail -3 | tee /tmp/m107/step3-ruff.txt
$V -m ruff format --check . 2>&1 | tail -2 | tee -a /tmp/m107/step3-ruff.txt
$V -m bandit -r . -ll -q 2>&1 | tail -8 | tee /tmp/m107/step3-bandit.txt; echo "bandit_exit=$?"

# اختیاری/تکراری: job `backend` در CI همین را **بلاکینگ** اجرا می‌کند (`pip-audit` بدون
# `|| true`) و سبز است. در مخزن lock وجود ندارد، پس عدد «سازگارترین نسخه‌های امروز» است؛
# آن را «pinned» گزارش نکن. این خط فقط برای وقتی است که می‌خواهی روی همان container خودت
# (یا پس از upgrade مشکوک) بازتولید کنی.
/tmp/m107/venv/bin/pip-audit 2>&1 | tail -25 | tee /tmp/m107/step3-pipaudit.txt
echo "pipaudit_exit=$?"
/tmp/m107/venv/bin/pip freeze > /tmp/m107/step3-freeze.txt   # برای اینکه معلوم باشد روی چه نسخه‌هایی سنجیده شد

# ۲) drift + مانور backup/restore روی DB **کش**ی (هیچ‌وقت DB production نه)
MP_DATABASE_URL=sqlite:////tmp/m107/drill.db $V -m alembic upgrade head 2>&1 | tail -3
$V -m alembic check 2>&1 | tail -3 | tee /tmp/m107/step3-alembic.txt
$V scripts/backup.py backup --out /tmp/m107/backup --db /tmp/m107/drill.db 2>&1 | tail -4
ARCH=$(ls -t /tmp/m107/backup/*.tar.gz | head -1)
$V scripts/backup.py verify "$ARCH" 2>&1 | tail -4 | tee -a /tmp/m107/step3-alembic.txt
$V scripts/backup.py restore "$ARCH" --db /tmp/m107/restored.db --extras-to /tmp/m107/extras 2>&1 | tail -4
git -C "$REPO" status --porcelain | tee /tmp/m107/step3-worktree-after.txt   # باید خالی باشد
```

`pip-audit` اگر چیزی پیدا کرد، **upgrade انجام نده**؛ لاگ + `step3-freeze.txt` را بفرست تا جدا تصمیم بگیریم (هر upgrade دامنهٔ خود را می‌خواهد).
`restore` نباید هیچ فایل زنده‌ای را تغییر دهد — `step3-worktree-after.txt` خالی، شاهدِ R-031 است. اگر `$V -m alembic check`
بگوید «New upgrade operations detected»، یعنی drift واقعی (مدل ≠ مهاجرت) و همان یک line را عیناً بفرست.

## ۴) گیت‌های Studio

```bash
cd "$(git rev-parse --show-toplevel)/mp-app/studio"
npm ci 2>&1 | tail -3 | tee /tmp/m107/step4-npmci.txt
npm test 2>&1 | tail -8 | tee /tmp/m107/step4-test.txt        # انتظار: 219 passed / 9 skipped
npm run build 2>&1 | tail -12 | tee /tmp/m107/step4-build.txt
npx vitest run tests/apiCoverage.test.ts 2>&1 | tail -5 | tee -a /tmp/m107/step4-test.txt
# عمداً: `npm run lint` در این مخزن اسکریپت دارد ولی dependency eslint ندارد → شکست آن یافتهٔ مستند است، نه باگ تو
npm run lint 2>&1 | tail -4 | tee /tmp/m107/step4-lint.txt || true
```

خروجی `build` (سایز chunk) را نگه دار: **بی‌اساس‌بودن حجم، یک بارِ ثبت‌شده در `LOOP-PLAN` است** و با تغییر بعدی مقایسه می‌شود.

## ۵) Android — «شاهد کامپایل» (M87 و lintVitalRelease)

دو راه، به ترتیب ترجیح:

**الف) بدون Codespace، در همان CI (دقیق‌ترین):** `apk.yml` روی `workflow_dispatch` است و کامل‌ترین کار را می‌کند
(pub get · analyze · test · `flutter build apk --release --split-per-abi` · بازرسی عمیق apktool).

```bash
gh workflow run apk.yml --ref arena/4f336f66-mp -f build_number=99
gh run watch "$(gh run list --workflow=apk.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
```

> **قبل از زدن این دستور بخوان:** این workflow با `android/keystore/keystore.properties` موجود در مخزن امضا می‌کند —
> همان پرونده‌ای که SEC-01 رویش قرمز است. خروجی آن **شاهد کامپایل/مانیفست** است، نه چیزی که باید نصب یا
> توزیع شود. اگر ترجیح می‌دهی تا چرخش کلید اصلاً بیلد امضاشده نساز، از راه (ب) استفاده کن.

**ب) در Codespace (بدون keystore، فقط debug):** تصویر عمداً Android SDK ندارد؛ اسکریپت اختیاریِ پین‌شده اضافه شده:

```bash
cd "$(git rev-parse --show-toplevel)"
# اسکریپت untested است (این sandbox به storage.googleapis.com دسترسی ندارد)؛ اگر مرحله‌اش شکست، لاگ را بفرست
ACCEPT_ANDROID_LICENSES=1 bash .devcontainer/provision-android-sdk.sh 2>&1 | tee /tmp/m107/step5-sdk.txt
flutter config --android-sdk "$HOME/android-sdk"
flutter doctor -v 2>&1 | tee /tmp/m107/step5-doctor.txt
cd mp-app/client
flutter build apk --debug 2>&1 | tail -20 | tee /tmp/m107/step5-build.txt; echo "exit=$?"
ls -la build/app/outputs/flutter-apk/ | tee -a /tmp/m107/step5-build.txt
```

شاهد مورد انتظار: کامپایل `MainActivity.kt` و `OfflineFeedbackDatabase.kt` (یعنی Kotlin + Gradle 9.5.0 + AGP 9.3.1
روی این منبع می‌سازد) — همان چیزی که برای **M87** کم بود و M88/M89 را بلوکه کرده بود.
`flutter doctor -v` را هم بفرست: اگر `platforms;android-XX` دیگری لازم شد، اسکریپت با
`SDK_PACKAGES="platforms;android-XX build-tools;XX.0.0" ACCEPT_ANDROID_LICENSES=1 bash …` قابل تکرار است.
اسکریپت در این sandbox **اجرا نشده** (دسترسی به `storage.googleapis.com` وجود نداشت) — پس اولین اجرا خودش یک گیت است: اگر checksum/download رد شد، `SDK_URL` و `SDK_SHA256` را از صفحهٔ رسمی Android Studio بردار و همان را به‌جای مقادیر پیش‌فرض env بده؛ مقدار حدسی **set نکن**.
پس از آن، اجرای دوبارهٔ `dart test` در پوشهٔ اندروید لازم نیست؛ **persist/restart فقط با گوشی معنی دارد (مرحلهٔ ۶).**

## ۶) دستگاه واقعی — روی لپ‌تاپ، نه در مرورگر

Codespace به USB دسترسی ندارد و emulator شتاب‌یافته (KVM) روی آن ندارد؛ پس این جدول را روی لپ‌تاپ
با repo همان sha و یک گوشی Android اجرا کن (`adb devices` باید یکی نشان دهد):

```bash
adb devices
adb install -r mp-app/client/build/app/outputs/flutter-apk/app-debug.apk
PKG=ir.muscleparadise.mp_client
```

| # | دستور | چه ثبت شود | loop |
|---|---|---|---|
| ۶-۱ | `adb shell am force-stop $PKG; adb shell am start -W -n $PKG/.MainActivity` × ۵ | `TotalTime` هر ۵ بار → **median cold start** | **M104** |
| ۶-۲ | `adb shell am start -W -n $PKG/.MainActivity` (بدون force-stop) × ۵ | median **warm start** | **M104** |
| ۶-۳ | `adb shell settings put global animator_duration_scale 0` (و `window_animation_scale`، `transition_animation_scale`) | ترنزیشن تب شل باید **بی‌حرکت** باشد؛ با `1.0` برگردان و مقایسه کن | **M98** (reduced-motion) |
| ۶-۴ | روی همان گوشی: ثبت بازخورد ست / لغو رزرو / افزودن به سبد / «ثبت سفارش» | آیا **سه پالس** (انتخاب/موفق/هشدار) حس می‌شوند و فرق دارند؟ | **M98** |
| ۶-۵ | فروشگاه ← «سفارش‌ها» ← «رسید» (با عضو واقعی/حساب آزمایشی) | screenshots: overflow نیست؟ ارقام فارسی‌اند؟ ارتفاع `0.78` شیت کم است؟ | **M90** |
| ۶-۶ | حالت تیره/روشن لانچر + صفحهٔ «همهٔ برنامه‌ها» | screenshot آیکن با **ماسک** (دایره/مربع/قطره) و نسخهٔ ۴۸dp | **M105/M106** |
| ۶-۷ | `AAPT=$(ls "$ANDROID_HOME"/build-tools/*/aapt2 \| head -1); "$AAPT" dump badging <apk> \| grep -iE 'icon\|round-icon\|package'` | آنچه **درون APK** است (نه آنچه در repo است): نام آیکن، mipmapهای موجود، `debuggable`، `minSdk/targetSdk` | **M106 / M60-manifest** |
| ۶-۸ | قطع شبکه (حالت پرواز) ← ثبت بازخورد ← وصل شدن | صف آفلاین باید **یک بار** ارسال شود و پیام «ثبت شد» قبل از ارسال نیاید | **M87/M86** |
| ۶-۹ | `adb shell input keyevent KEYCODE_WAKEUP` + QR پذیرش (اگر M69 روشن شد) | scan مجاز/تکراری/QR عضو دیگر | **M89** |

برای ۶-۸ دقت کن: feature flag outbox پیش‌فرض خاموش است؛ برای سنجش، همان flag را در build debug روشن کن
(نه در کد commit‌شده). جزئیات: `docs/MuscleParadise/ANDROID-OFFLINE-PLAN.md`.

## ۷) پاک‌سازی

```bash
gh codespace stop -C <CODESPACE_NAME>        # هزینه متوقف می‌شود؛ ماشین می‌ماند
gh codespace delete -C <CODESPACE_NAME> --force   # اگر دیگر لازم نداری
```

## ۸) چه چیزی را برای من بفرست (قالب)

```text
sha=<HEAD>            flutter=<frameworkVersion/revision>   java=<...>
step2-analyze: exit=… | «No issues found!» یا خلاصهٔ خط‌ها
step2-test:    exit=… | <N> passed, <N> failed, <N> skipped   ← عدد، نه «معمولاً سبز است»
step3-pytest:  exit=… | <N> passed / <N> skipped
step3-pipaudit:exit=… | <X> known vulnerabilities در <Y> dependencies | یا: «no known vulnerabilities found»
step5-build:   exit=… | Built build/app/outputs/flutter-apk/app-debug.apk (+ اندازه)
step6-1..6-3:  پنج عدد TotalTime + median | تفاوت animator 0 و 1.0
step6-4..6-6:  «حس شد/نشد» + مسیر screenshotها
```

من بر اساس همین‌ها وضعیت را عوض می‌کنم: `M90/M98` از «PASS (client CI)» به «PASS + device verified»،
`M104` از `UNKNOWN` به عددِ ثبت‌شده، `M87` برای بُعد کامپایل، و اگر چیزی قرمز شد یک loop رفع با شاهد.
**عدد حدسی، «روی شبیه‌ساز دیده شد»، یا «لاگش پیش من نیست» هیچ‌کدام وضعیت را عوض نمی‌کنند.**

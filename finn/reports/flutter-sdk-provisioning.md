# بررسی و تلاش فراهم‌سازی Flutter/Dart در sandbox

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ commit/push انجام نشد)
- نتیجه: نصب Flutter/Dart در این sandbox ممکن نشد؛ آرشیو SDK را دانلود یا extract نکردم و متغیرهای محیطی را تغییر ندادم.

## وضعیت میزبان و تلاش نصب

- میزبان Linux `x86_64` است. `flutter`, `dart`, `dartaotruntime`, Java/Javac، Android `sdkmanager`/`adb` و container runtimeها (Docker/Podman/Buildah/Skopeo) پیدا نشدند.
- `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `PUB_CACHE`, `PUB_HOSTED_URL` و `FLUTTER_STORAGE_BASE_URL` خالی‌اند. در مسیرهای متداول SDK و cache، `flutter`/`dart`, `.pub-cache`, `.dart_tool` یا `pubspec.lock` پیدا نشد.
- mirrorهای Flutter در جست‌وجوی بیرونی پاسخ metadata می‌دهند؛ اما اتصال shell همین sandbox به mirrorها در handshake TLS با `curl (35) SSL_ERROR_SYSCALL` قطع می‌شود. برای آرشیو واقعی CFUG، درخواست آزمایشی Range یک‌بایتی نیز صفر بایت و همین خطا داد. درخواست GitHub به‌عنوان کنترل `HTTP 200` داشت. این شواهد، محدودیت egress همین محیط را نشان می‌دهد و به‌تنهایی خرابی mirrorها را ثابت نمی‌کند.
- فرمان‌های `flutter --version`, `flutter pub get --offline`, `flutter analyze --no-fatal-infos`, `flutter test` و `flutter build apk --release` همگی با exit 127 (فرمان موجود نیست) تمام شدند. APK موجود جایگزین اجرای سورس یا تست نیست.

## انتخاب mirror و تطبیق metadata

**انتخاب پیشنهادی در صورت بازشدن دسترسی شبکه: CFUG** — مستندات Flutter این mirror جامعه‌ای را در فهرست mirrorهای trusted آورده و زوج `PUB_HOSTED_URL`/`FLUTTER_STORAGE_BASE_URL` را مستند کرده است: <https://docs.flutter.dev/community/china>.

- metadata آرشیو رسمی و metadata CFUG برای stable برابر Flutter `3.50.0`, revision `ab2912035e160d9cad6306df307576da6128ebdb`, Dart `3.14.0` و SHA-256 زیر است:
  `6ea2d806fd57269ae783e6788e2a81fc26eaad782f1e0d0ff38623bb765ff9f5`
- metadata Runflare نیز همین stable revision و checksum را نشان داد؛ endpointهای مستندشده‌اش جدا هستند: `mirror-flutter.runflare.com` برای Pub و `mirror-gcs.runflare.com` برای Flutter storage.
- metadata Myket در زمان بررسی از نسخهٔ stable `3.47.9` با revision `c197ca5199e9ee5661e865596c9c07294dfab51c` و checksum `25ed8c3c29d51a7353f2a944310b478af8214920639524b19c50a19e6c044c5a` جلوتر نرفته بود؛ نسبت به stable فعلی `3.50.0` عقب است.
- طبق جدول پوشش خود <https://github.com/IR-Flutter/PackageDownloader>، PUB-AZS برای Dart/Pub است، نه Flutter Storage؛ پس به‌تنهایی SDK/artifactها را فراهم نمی‌کند.
- Myket مستندات خودش `pub.myket.ir` را برای package و آرشیوهای Flutter و `maven.myket.ir` را جداگانه برای Gradle معرفی می‌کند. این ادعاها از داخل sandbox به دانلود واقعی منتهی نشدند.
- **checksum آرشیو را داخل sandbox محاسبه نکردم**، چون بایت‌های آرشیو دریافت نشدند؛ تنها metadata mirror با metadata upstream تطبیق داده شد. چیزی نصب یا به PATH اضافه نشده است.

## بررسی GitHub، Hugging Face و package registryها

- مخزن <https://github.com/mes-systems/containerized-flutter> برای Linux amd64 تصویر SDK با نسخه/checksumهای pinشده معرفی می‌کند، اما خروجی‌اش GHCR است؛ GitHub Release asset ندارد و هیچ container runtime در میزبان موجود نیست. تصویر همچنین JDK و Android SDK ندارد، پس به‌تنهایی APK build را ممکن نمی‌کرد.
- مخازن prebuilt بررسی‌شدهٔ قبلی ARM64 بودند و با میزبان x86_64 سازگار نیستند. در جست‌وجوی repoها، آرشیو مستقل و معتبر Linux x64 برای نصب مستقیم پیدا نشد.
- جست‌وجوی Hugging Face برای `flutter-sdk`/`dart-sdk` در models/datasets/Spaces نتیجهٔ SDK/toolchain نداد؛ جست‌وجوی عمومی `flutter` مدل‌ها/دیتاست‌های کد و ML برگرداند، نه runtime.
- در PyPI پروژه‌های `flutter-sdk` و `dart-sdk` وجود نداشتند؛ در npm هم همین نام‌ها 404 شدند. packageهای هم‌نام `flutter` و `dart` در npm/PyPI ابزار زبان نیستند (از جمله Twitter OAuth و ابزار تبدیل داده/متغیر URL)، بنابراین نصب نشدند.

## تلاش مجددِ ترتیبی برای همهٔ منابع (به درخواست کاربر)

هر منبعِ دارای Flutter Storage، جداگانه و با URL آرشیو/manifest واقعی آزمایش شد؛ دانلود کامل را فقط پس از موفقیت اتصال و امکان بررسی checksum ادامه می‌دادم. در این نوبت GET یک‌بایتی `Range: 0-0` برای upstream، Runflare، Myket و TarazERP هم اجرا شد؛ همه پیش از دریافت byte اول با TLS شکست خوردند (0 bytes). برای CFUG نیز تلاش قبلی Range و تلاش فعلی `wget --spider` شکست خورد. هیچ آرشیوی ناقص/غیرقابل‌اعتبارسنجی نصب نشد.

| منبع | درخواست واقعی | نتیجه در sandbox |
|---|---|---|
| upstream Google | `storage.googleapis.com/.../flutter_linux_3.50.0-stable.tar.xz` | `curl`: `SSL_ERROR_SYSCALL`، exit 35 |
| Flutter China / CFUG | `storage.flutter-io.cn/.../flutter_linux_3.50.0-stable.tar.xz` | `wget`: اتصال TCP برقرار شد، TLS غیرعادی قطع شد، exit 4 |
| Runflare | `mirror-gcs.runflare.com/.../flutter_linux_3.50.0-stable.tar.xz` | `curl`: `SSL_ERROR_SYSCALL`، exit 35 |
| Myket | `pub.myket.ir/.../flutter_linux_3.47.9-stable.tar.xz` | `curl`: `SSL_ERROR_SYSCALL`، exit 35 |
| TarazERP | `flutter.tarazerp.ir/.../flutter_linux_3.41.4-stable.tar.xz` | `wget`: اتصال TCP برقرار شد، TLS غیرعادی قطع شد، exit 4؛ manifest قابل‌مشاهده با fetch tool فقط stable قدیمی 3.41.4/Dart 3.11.1 را نشان می‌دهد (قید Dart پروژه را برآورده می‌کند، اما فایل آرشیو قابل‌دریافت نبود) |
| PUB-AZS | Flutter Storage path در registry این منبع غیرفعال/unsupported و طبق گزارش ناشر 404 است؛ درخواست shell نیز `SSL_ERROR_SYSCALL` داد | منبع نصب Flutter SDK نیست |

برای **Pub packages** نیز endpointهای رسمی `pub.dev` و mirrorهای Myket، TarazERP، Runflare، Flutter China و PUB-AZS، تک‌به‌تک با درخواست `/api/packages/http` آزمایش شدند؛ همه با `SSL_ERROR_SYSCALL`/TLS termination شکست خوردند. پس حتی اگر آرشیو SDK از راه دیگری در دسترس بود، dependency resolution از شبکهٔ فعلی ممکن نبود.

منبع دیگرِ GitHub، `IR-Flutter/PackageDownloader`، فهرست mirrorهای Flutter Storage را برای Myket/TarazERP/Runflare/Flutter China معرفی می‌کند و PUB-AZS را صریحاً فاقد SDK storage می‌داند. metadata/release API از `api.github.com` پاسخ داد، اما دریافت `pdown-linux-x64` و `checksums.txt` از release به `release-assets.githubusercontent.com` هدایت و با EOF شکست خورد؛ `rustc`/`cargo` هم نصب نیستند تا source آن build شود. GitHub Releases خود Flutter فقط تا Flutter 3.19 beta (2024) فهرست شد و آرشیو Stable 3.50.0 ندارد. مخزن `mes-systems/containerized-flutter` release asset ندارد و تصویرش به GHCR/container runtime نیاز دارد؛ runtime محلی موجود نیست.

registryهای مجازِ package-manager نیز جایگزین SDK نبودند: `npm view flutter-sdk` و `npm view dart-sdk` هر دو 404؛ PyPI برای هر دو `No matching distribution found`. مخزن Hugging Face که قبلاً بررسی شد نیز runtime/toolchain نداشت. منابع Maven/Gradle (Myket/TarazERP/Aliyun و مشابه) فقط وابستگی‌های build را mirror می‌کنند، نه Flutter/Dart SDK یا Android SDK.

**نتیجهٔ این دور:** از هیچ منبعی فایل قابل‌نصب حاصل نشد؛ checksum آرشیو واقعی از این sandbox قابل‌محاسبه نیست و هیچ M78/M79/M80 Flutter runtime اجرا نشد. شکست‌های قبلی پنج فرمان Flutter به exit 127 (نبود executable) همچنان معتبرند.

## ارزیابی آفلاین و Gradle

- `flutter pub get --offline` فقط از Pub cache محلی استفاده می‌کند. این میزبان cache، `.dart_tool` یا lockfile ندارد؛ بنابراین حتی با دسترسی به خود Flutter نیز این روش در وضعیت فعلی حل‌کننده نیست. این فرمان SDK یا Maven/Gradle artifact تولید نمی‌کند.
- `gradle_repo_manager` یک Dart package است (SDK constraint از 3.0 به بالا) و برای یافتن SDK، `flutter doctor -v` اجرا می‌کند؛ نمی‌تواند Flutter را bootstrap کند. اسکنر آن `**/*.gradle` را هدف می‌گیرد، اما پروژهٔ Android ما از `settings.gradle.kts` و `build.gradle.kts` استفاده می‌کند؛ پس ابزار به فایل‌های این پروژه نمی‌رسد.
- حتی پس از نصب Flutter، `flutter build apk` در میزبان فعلی به‌دلیل نبود Java و Android SDK قابل اجرا نیست.

## آزمون‌هایی که توانستم انجام دهم

- تست‌های تمرکزی M80/ownership/feed/RBAC: **57 passed**.
- کل backend suite (اجرا از پوشهٔ `mp-app/backend` مطابق CI): **811 passed, 1 skipped**. اجرای اول از ریشهٔ repo دو مشکل محیط/شاهد نشان داد: یک تست به cwd backend وابسته بود و `api/routes.json` مسیر M80 را نداشت. با اجرای از cwd مورد انتظار و بازتولید artifact با `scripts/export_routes.py`، suite سبز شد.
- `ruff check .`, `ruff format --check .` و `py_compile` سبز. برای سبزشدن format gate هشت فایل صرفاً formatting شدند؛ تغییر منطقی ندارند.
- Dart static gate: **55 فایل، 0 یافته**؛ manifest gate: **1 مانیفست، 0 یافته**. این دو جایگزین `flutter analyze`, `flutter test` یا build نیستند.

## GitHub Actions و گام بعدی

- Workflow محلی `.github/workflows/ci.yml`، job به‌نام `client-flutter` دارد که stable Flutter را نصب و `pub get`, analyze, کل `flutter test` و manifest gate را اجرا می‌کند. اسکریپت `mp-app/client/ci_apk.sh` نیز build APK دارد، ولی در این workflow فراخوانی نمی‌شود.
- در origin، شاخهٔ جاری `arena/4f336f66-mp` وجود ندارد و upstream تنظیم نشده؛ `gh run list --branch arena/4f336f66-mp` خالی بود. runهای موجودی که روی شاخهٔ دیگری هستند شاهد این کد محسوب نمی‌شوند. من تغییرات را commit/push نکردم؛ بنابراین GitHub Actions روی این workspace اجرا نشد.
- برای اجرای runtime داخل همین sandbox، باید دسترسی egress به mirror منتخب/مخزن Pub باز شود؛ برای APK build باید Java و Android SDK هم فراهم باشند. یا باید تغییرات فعلی به شاخهٔ جاری remote برسند تا jobهای GitHub روی همین نسخه اجرا شوند. M80 به‌دلیل اجرا نشدن Flutter runtime همچنان `UNKNOWN` است.

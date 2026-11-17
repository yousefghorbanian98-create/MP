# M87 — Android outbox برای بازخورد ساختاریافتهٔ تمرین

- تاریخ: 2026-11-16
- وضعیت: **UNKNOWN** — کد/آزمون منبع نوشته شده؛ Flutter/Dart و Android/Kotlin runtime در sandbox در دسترس نیست.
- دامنهٔ API: فقط `POST /programs/sync/set-feedback` از قرارداد M86.

## پیاده‌سازی ثبت‌شده

- فایل `android/app/src/main/kotlin/ir/muscleparadise/mp_client/OfflineFeedbackDatabase.kt` از SQLite داخلی Android و DB خصوصی app استفاده می‌کند؛ `MainActivity.kt` یک MethodChannel کوچک برای store و وضعیت شبکه دارد. dependency سوم‌طرفه‌ای اضافه نشده است.
- payload در Dart و Kotlin allowlist می‌شود: owner از نشست، client/device ID تصادفی، program/movement، weight/reps، RIR و timestamp ثابت UTC. `soreness`, notes، credential، response خام و owner آزاد وارد رکورد/درخواست نمی‌شوند.
- شناسه و timestamp اصلی برای retry ثابت می‌مانند. Batch حداکثر 100، `created_at,id`، owner predicate، per-item response validation، `unchanged_keys` duplicate ACK، conflict/stale/clock-skew و retryهای محدود با backoff پیاده‌سازی شده‌اند. پس از 5 شکست نیاز به retry صریح کاربر دارد؛ background worker وجود ندارد.
- UI پیام pending را فقط بعد از write محلی نشان می‌دهد و صفحهٔ Today وضعیت pending/retry/failed/conflict/synced، sync، manual retry و discard تأییدشده را دارد. fallback تنها وقتی Android نبود شبکه را گزارش کند فعال می‌شود؛ timeout/5xx مسیر online خودکار در queue تکرار نمی‌شود چون احتمال commit نامعلوم است.
- صف با member owner جدا می‌شود. Logout/تغییر شماره در صورت دادهٔ حل‌نشده نیازمند انتخاب نگه‌داشتنِ همان owner یا حذف صریح است؛ account دیگر نمی‌تواند آن صف را sync کند.
- Feature flag `MP_ANDROID_OFFLINE_FEEDBACK_ENABLED` در Dart پیش‌فرض `false` است. `allowBackup=false` فعال است؛ هیچ app-layer encryption یا attestation رمزنگاری دستگاه ادعا/پیاده‌سازی نشده است. فقط پس از بررسی سیاست دستگاه/محیط می‌توان build مدیریت‌شده را صریحاً فعال کرد.

## تطبیق قرارداد API و program ID

- در checkout حاضر، `POST /programs/sync/set-feedback` در `modules/programs/router.py` ورودی `SyncIn` می‌گیرد: `member_id` و `items`؛ `SyncItemIn` فیلد `program_id` و فیلدهای ساختاریافتهٔ موردنیاز outbox را می‌پذیرد. `modules/programs/service.py::sync_set_feedback` پاسخ را با `member_id` برمی‌گرداند، `results` و `counts.received` را از `resolve_batch` حفظ می‌کند و همیشه `unchanged_keys` را هم در response نهایی می‌گذارد. پس شرط parser برای پاسخ سرور با source contract سازگار است. تست integration اکنون `member_id`، `counts.received` و لیست خالی `unchanged_keys` را نیز assert می‌کند.
- `GET /programs/member/{member_id}` از `list_member_programs` می‌آید که برنامه‌ها را با `id DESC` مرتب می‌کند؛ `ProgramOut` شامل `id` است. `myProgramsProvider` همان فهرست را می‌خواند، `activeProgramProvider` از `list.first` استفاده می‌کند و `todayExercisesProvider` تمرین‌ها را از همان برنامه می‌گیرد. `TodayPage` نیز برای feedback همان `programs.first['id']` را می‌فرستد؛ بنابراین source ID با برنامه‌ای که تمرین‌های امروز از آن نمایش داده شده منطبق است. این تأیید source-level است، نه Flutter runtime evidence.

## آزمون‌های نوشته‌شده و محدودیت شاهد

`test/offline_feedback_outbox_test.dart` سناریوهای allowlist، stable device ID، fixed-width timestamp، owner binding و response-owner mismatch، duplicate با `unchanged_keys`، stale conflict، 5xx retry/error-code redaction، auth، response ناقص، و انتخاب logout/discard را پوشش می‌دهد.

این تست‌ها در این نوبت **اجرا نشده‌اند**؛ Flutter/Dart executable در sandbox وجود ندارد. Native SQLite restart/write-read، Kotlin compile، Android device lifecycle، plugin/channel round-trip و end-to-end قطع/وصل نیز آزموده نشده‌اند. بنابراین M87 `PASS` نیست و خروجی static Dart gate هم جایگزین runtime محسوب نمی‌شود.

### Validation قابل‌اجرا در sandbox در 2026-11-16

- `PYTHONPATH=/tmp/mp-m87-static python3 tools/dart_gate.py --include-tests` → **64 فایل Dart، 0 یافته** (گیت Tree-sitter/source؛ نه type analysis، formatter یا runtime).
- `python3 tools/manifest_gate.py` → **1 مانیفست، 0 یافته**؛ Tree-sitter Kotlin source parse → **2 فایل Kotlin، 0 خطای syntax** (این کامپایل یا type-check نیست).
- Backend هدفمند برای M84 class booking/cancel/finance + M57 sync → **20 passed، 2 هشدار**؛ شامل assertionهای قرارداد پاسخ M86 و سناریوهای نام/مالکیت M84.
- گیت کامل backend: `pytest --cov=. --cov-report=term --cov-fail-under=70` → **853 passed, 2 skipped**، پوشش **86.30%** (حد 70%)؛ `ruff check .` و `ruff format --check .` برای کل backend پاس شدند.
- Workflow YAML parse شد و هر **23** اسکریپت shell توکار `bash -n` را گذراند؛ `git diff --check` نیز پاس شد.
- `flutter`, `dart`, `java`, `gradle` و `kotlinc` در sandbox موجود نیستند؛ پس `flutter format/analyze/test`، Kotlin compile، Gradle/Android build، round-trip بومی SQLite/MethodChannel و persistence/restart روی دستگاه اجرا نشدند. گیت Tree-sitter/source و backend جایگزین این runtime gateها نیستند.
- CI `44198198864` روی commit `b7cd7f1` source M84–M87 را آزمود. Backend پاس شد؛ analyzer fail شد، client tests skip شدند، و Studio API coverage به‌دلیل TODO کهنه fail شد. علت‌های analyzer و Studio exception در `0ace8fe` اصلاح شدند؛ run CI جدید `44200381791` backend/Studio/live-contract/e2e-api را پاس کرد و Studio API coverage را تأیید کرد.
- در `44200381791`، `flutter analyze` هنوز به‌دلیل warning `UNUSED_ELEMENT_PARAMETER` برای `_MemoryStore.network` شکست خورد؛ client tests و manifest gate skip شدند. Patch جاری از `_MemoryStore(network: false)` در تست `offlineFeedbackNetworkAvailableProvider` استفاده می‌کند تا این warning رفع و رفتار offline-status پوشش داده شود. Flutter/Dart محلی نیستند و این تست اجرا نشده؛ analyzer و client tests منتظر CI بعدی‌اند. Gitleaks نیز به‌دلیل همان matchهای تاریخی fail مانده. جزئیات redacted: `finn/reports/ci-follow-up-441922-441942.md`.

## بازتولید در Codespaces

پس از انتخاب/ساخت Codespace توسط کاربر روی branch مجاز، در `mp-app/client` اجرا شود:

```bash
flutter pub get
flutter analyze --no-fatal-infos
flutter test test/offline_feedback_outbox_test.dart
flutter test
```

این‌ها Dart/Widget behavior را می‌سنجند، نه Kotlin/native SQLite. اعتبارسنجی Android واقعی به Android SDK و دستگاه/emulator جداگانه نیاز دارد. تا آن زمان feature flag خاموش بماند.

## بازگشت

فایل‌های M87: Dart outbox/provider/UI/test، `MainActivity.kt`, `OfflineFeedbackDatabase.kt`, permission `ACCESS_NETWORK_STATE`, و ردیف/گزارش M87. قبل از rollback هر دادهٔ محلی باید با کاربر/دستگاه مدیریت‌شده حل شود؛ این بسته در Git هیچ DB محلی یا artifact/credential ندارد.

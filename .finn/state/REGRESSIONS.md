# FINN Regressions — رجیستری تست‌های رگریشن
> هر باگ رفع‌شده = حداقل یک تست رگریشن اینجا ثبت و در همهٔ چرخه‌های بعدی اجرا می‌شود.
| شناسه تست | مسیر فایل تست | باگ مرتبط | تاریخ افزودن | وضعیت |
|-----------|----------------|-----------|---------------|--------|
| R-001 | mp-app/backend/tests/regression/test_branch_id.py | دام M03: فراموشی branch_id در جدول‌های اصلی | 2026-11-14 | ✅ سبز |
| R-002 | mp-app/backend/tests/unit/test_models.py::test_otp_stores_hash_not_plain | دام M08: ذخیرهٔ خام OTP (پیشگیرانه) | 2026-11-14 | ✅ سبز |
| R-003 | mp-app/backend/tests/unit/test_crypto.py | NFR-3: رمزنگاری embedding چهره | 2026-11-14 | ✅ سبز |
| R-004 | mp-app/backend/tests/integration/test_api_contract.py (client fixture: limiter.reset) | آلودگی شمارندهٔ rate-limit بین تست‌ها (شکست در اجرای کامل) | 2026-11-14 | ✅ سبز |

## R-005. کش، چک مالکیت را دور می‌زد (M18)
مسیر early-return کش در `get_member` قبل از `ensure_member_scope` اجرا می‌شد ← عضو با کش گرم می‌توانست پروفایل دیگران را بخواند (۲۰۰ به‌جای ۴۰۳). تست دائمی: `test_member_cannot_read_other_members_data`. قانون: **هر گارد دسترسی باید قبل از هر cache-read باشد.**

| R-006 | `docs/MuscleParadise/finn/install-toolchain.sh` (خودآزمای `bash -n` + اجرای واقعی) | D-025: پین روی فورک منسوخ + نبود بازتولیدپذیری ابزار | 2026-11-15 | ✅ فعال — در فاز ۰ هر نشست اجرا/بررسی می‌شود |
| R-007 | `.finn/ecc-commit.txt` باید با `git -C .finn/ecc rev-parse HEAD` و بالادست `affaan-m/ECC` بخواند | D-025: انحراف منبع ECC | 2026-11-15 | ✅ فعال |
| R-008 | وجود `.claude/agents/{planner,architect,tdd-guide,code-reviewer,security-reviewer,build-error-resolver,e2e-runner,refactor-cleaner,doc-updater}.md` | D-025: نصب ناقص ایجنت‌ها | 2026-11-15 | ✅ فعال (خود اسکریپت هم چک می‌کند) |
| R-009 | وجود `.claude/skills/reverse-engineer-anything/SKILL.md` | D-026: REA بدون skill | 2026-11-15 | ✅ فعال |
| R-010 | `tests/integration/test_m45_admin_attendance.py` (۹ تست) | M45: endpoint حضور/خلاصهٔ اعضا نبود؛ `days_left` کف می‌گرفت (۳ روز → ۲) | 2026-11-15 | ✅ فعال |
| R-011 | `tests/integration/test_m45_programs_list.py` (۵ تست) | M45: صفحهٔ برنامه‌ها mock بود و فهرست برنامه در API نبود | 2026-11-15 | ✅ فعال |
| R-012 | `tests/integration/test_m45_checkin_feed.py` (۵ تست) | M45: جریان ورودها mock بود؛ ورود رد‌شده پنهان می‌شد | 2026-11-15 | ✅ فعال |
| R-013 | `tests/api.test.ts` (۷ تست استودیو) | M45: کلاینت API نباید در خطا به mock برگردد؛ null ≠ ۰ | 2026-11-15 | ✅ فعال |
| R-014 | assistant هیچ‌کدام از workflowها نباید شاخهٔ ثابت داشته باشد | CI به `arena/a0408b29-mp` هاردکد بود → روی شاخهٔ جاری diagnostics را push نمی‌کرد | 2026-11-15 | ✅ فعال (`github.head_ref \|\| github.ref_name`) |
| R-015 | `mp-app/backend/tests/integration/test_m65_qr_security.py` (۶ سناریو) | SEC-02: QR دور می‌زدن membership، ownership، replay را می‌پذیرفت و access-token بود | 2026-11-16 | ✅ سبز — 65 تست مرتبط |
| R-016 | `mp-app/studio/tests/session.test.ts`, `authFlow.test.tsx`; `mp-app/backend/tests/integration/test_m67_studio_auth.py` | M67: logout فقط refresh را revoke می‌کرد و access JWT همان نشست پس از logout هنوز 200 می‌داد | 2026-11-16 | ✅ سبز — pre-fix 200 بازتولید شد؛ post-fix rotation/logout access/refresh را رد می‌کند |
| R-017 | `mp-app/studio/tests/session.test.ts` | پاسخ دیررس refresh پس از logout نشست قبلی را بازمی‌گرداند؛ پاسخ دیررس logout یا 401 دیررس retry نشست تازه را پاک می‌کرد؛ refresh ناموفق قدیمی نیز tokenهای تازهٔ tab مشترک را پاک می‌کرد | 2026-11-16 | ✅ سبز — چهار regression پیش از fix fail شدند؛ generation/token guard و logout بدون پاک‌سازی دیرهنگام آن‌ها را می‌بندد |
| R-018 | `mp-app/studio/tests/apiCoverage.test.ts` | گیت مصرف API ممکن بود comment/string را call حساب کند، پارامتر dynamic client را به segment ثابت route تعمیم دهد، یا exception کهنه را نگه دارد | 2026-11-16 | ✅ سبز محلی — probeهای fake path، dynamic/conditional path و invoice-vs-receipt؛ تمام 114 path یا call دارند یا exception مستند |
| R-019 | `mp-app/client/test/membership_test.dart`, `home_banner_test.dart` | M72: تاریخ پایان/مرز انقضا، no-membership در برابر payload نامعتبر، یا ادعای روز خارج از قرارداد API | 2026-11-16 | 🟡 تست‌ها اضافه شدند؛ Flutter/Dart runtime موجود نیست، اجرا نشده (M72 `UNKNOWN`) |
| R-020 | `mp-app/backend/tests/unit/test_food_catalog_import.py`, `backend/tests/integration/test_m49_food_logging.py`, `client/test/nutrition_food_log_test.dart` | M73: member نتواند غذای خود را ثبت کند، مالکیت را دور بزند، منبع غیرایرانی/مجوزنامشخص وارد شود یا مقدار/جمع روز غلط باشد | 2026-11-16 | ✅ backend/data 25 passed؛ client widget نوشته‌شده اما Flutter runtime ندارد (M73 `UNKNOWN`) |
| R-021 | `mp-app/backend/tests/integration/test_m74_class_cancel.py`, `mp-app/client/test/classes_cancel_test.dart` | M74: member نتواند رزرو خودش را لغو/فرد منتظر را ارتقا دهد، cross-member book/cancel یا duplicate cancel پذیرفته نشود و ظرفیت تازه شود | 2026-11-16 | ✅ backend/RBAC 46 passed؛ client widget نوشته‌شده اما Flutter runtime ندارد (M74 `UNKNOWN`) |
| R-022 | `mp-app/backend/tests/integration/test_m75_notifications.py`, `mp-app/client/test/notifications_page_test.dart`, `client/test/home_page_test.dart` | M75: cross-member inbox/read ممنوع؛ inbox سه اعلان، unread/read، empty/error/retry و badge بر اساس API واقعی | 2026-11-16 | ✅ backend/reminder/chat/RBAC 65 passed؛ client widget tests نوشته و static بررسی شدند اما Flutter runtime ندارد (M75 `UNKNOWN`) |
| R-023 | `mp-app/client/test/readiness_card_test.dart`; backend `test_readiness.py`, `test_m48_feedback_applied.py` | M76: score صرفاً از API/feedback واقعی؛ `readiness=null` صفر نشود؛ signal نامعلوم، توصیه، loading/error/retry و disclaimer برآورد | 2026-11-16 | ✅ 22 readiness unit/integration passed (7 deselected)؛ Client widget test نوشته و static بررسی شد اما Flutter runtime ندارد (M76 `UNKNOWN`) |
| R-024 | `mp-app/client/test/volume_card_test.dart`; backend `test_m48_volume_api.py`, `test_load_attribution.py` | M77: source planned vs reported hard sets، level و MV/MEV/MAV/MRV درست؛ empty/error/retry و مالکیت عضو، بدون حجم mock | 2026-11-16 | ✅ backend volume/attribution 13 passed؛ Client widget test نوشته و static بررسی شد اما Flutter runtime ندارد (M77 `UNKNOWN`) |
| R-025 | `mp-app/backend/tests/integration/test_m78_adaptive_nutrition_client.py`, `backend/tests/integration/test_m49_adaptive_nutrition.py`, `client/test/adaptive_nutrition_test.dart` | M78: عضو وزن خودش را ثبت کند و دیگری را نه؛ TDEE/delta از report؛ insufficient data = null/none؛ weight/refetch/error/retry/no clinical advice | 2026-11-16 | ✅ backend adaptive/RBAC 74 passed؛ Client widget test نوشته و static بررسی شد اما Flutter runtime ندارد (M78 `UNKNOWN`) |
| R-026 | `mp-app/client/test/bodycomp_real_data_test.dart` | M79: نمودار روند عضو فقط از حداقل دو اندازه‌گیری واقعی JP7 ساخته شود؛ با یک نقطه chart جعلی نباشد و تاریخ‌های API بدون خطای تبدیل نمایش داده شوند | 2026-11-16 | 🟡 تست/کد افزوده و static Dart 53/0؛ Flutter runtime اجرا نشده (M79 `UNKNOWN`) |
| R-027 | `mp-app/backend/tests/integration/test_m80_member_checkin_history.py`, `mp-app/backend/tests/regression/test_rbac.py`, `mp-app/client/test/member_checkin_history_test.dart` | M80: member history فقط از user جاری؛ تزریق `member_id` به مسیر self با 403 رد شود، نشت عضو دیگر و دسترسی به `/admin/checkins` بسته بماند؛ denied/empty/error/retry/pagination درست بمانند | 2026-11-16 | ✅ backend کل 811 passed/1 skipped؛ Dart static 55/0؛ Flutter widget runtime اجرا نشده (M80 `UNKNOWN`) |

## M61 — چهار رگرسیون جدید

| باگ | تست | اگر رفع برگردد |
|---|---|---|
| D1 دکمهٔ ثبت چهره ۴۰۳ برای member | `backend/tests/integration/test_m61_face_member_gate.py` (۴ تست) | با حذف ردیف rbac، ۳ تست قرمز می‌شود (اثبات‌شده) |
| D2 بدنهٔ چک‌این ۴۲۲ | `client/test/face_consent_gate_test.dart` | تست شکل بدنه (`method: face`، بدون `image_base64`) |
| D3 نبود logout | `client/test/logout_test.dart` + `logout_button_test.dart` | توکن پاک نشود یا مسیر سرور صدا زده نشود |
| D6 گیت دروغ‌گو | `studio/tests/apiCoverage.test.ts` | evidence ناموجود → قرمز (اثبات‌شده) |
| D7 VolumePanel روی items[0] | `studio/tests/programsPage.test.tsx` (۲ تست) | درخواست به `/member/7/` برود → قرمز |

## R-028 (M81 + اصلاح scanner M71)

- تست‌ها: `mp-app/client/test/member_chat_page_test.dart`, `mp-app/client/test/home_page_test.dart`, `mp-app/studio/tests/apiCoverage.test.ts`; قرارداد backend موجود: `mp-app/backend/tests/integration/test_m51_chat.py`.
- رگرسیون‌ها: فهرست چت بدون `member_id` caller؛ دادهٔ خارج از `memberId` نشست رد می‌شود؛ empty/error/retry، thread، read، send، حفظ draft در failure و بسته‌بودن گفتگو؛ routeهای provider-chain در گیت M71 مصرف واقعی شمرده شوند.
- وضعیت: backend chat **13 passed**؛ M71 targeted **4 passed**, Studio **217 passed/9 skipped**, build سبز؛ Dart static **58/0**. Flutter widget/runtime اجرا نشده و M81 همچنان `UNKNOWN` تا Codespaces.

## R-029 (M82) — تغییر امن شمارهٔ ورود با اثبات هر دو شماره

- تست‌ها: `mp-app/backend/tests/integration/test_m82_phone_change.py`، `mp-app/client/test/phone_change_dialog_test.dart`، `mp-app/studio/tests/phoneChange.test.tsx`؛ گیت session Studio: `studio/tests/session.test.ts`.
- رگرسیون‌ها: هر دو OTP به ترتیبِ شمارهٔ فعلی و جدید؛ کد نادرست 400 بدون refresh/retry نشست؛ challenge user-scoped، TTL، سقف تلاش/ابطال و replay؛ شمارهٔ تکراری قبل/بعد از درخواست و unique constraint race؛ OTP hash-only؛ لغو refresh و access JWTهای همهٔ نشست‌ها، از جمله legacy بدون `sid` و `ver`; ورود دوباره با شمارهٔ جدید همان حساب را resolve می‌کند؛ Client بعد از موفقیت logout و `/otp`، Studio sign-out. همهٔ SMS با provider جعلی capture شدند؛ تماس واقعی انجام نشد.
- وضعیت: backend M82 **8 tests** و کل suite **810 passed / 2 skipped**؛ route guard regression و Ruff سبز؛ Studio full **219 passed / 9 skipped** + build؛ Dart static **60 فایل / 0 یافته**. Flutter widget/analyze/pub-get/APK اجرا نشده چون Flutter/Dart/Java/Android SDK حاضر نیست؛ M82 برای Client runtime `UNKNOWN` است.

## R-030 (M83) — دفتر کیف‌پول از transaction ledger واقعی و محدود به عضو

- تست‌ها: `mp-app/backend/tests/integration/test_m83_wallet_ledger.py`; `mp-app/client/test/wallet_history_test.dart`; API coverage در `mp-app/studio/tests/apiCoverage.test.ts`.
- رگرسیون‌ها: payment history را معادل wallet ledger فرض نکن؛ credit/debit واقعی از `wallet_transactions`، مانده و page rows با یک statement، ترتیب پایدار `id DESC` و cursor `< before_id`؛ عضو فقط دفتر خود، staff برای حساب‌های مجاز audit؛ دفتر خالی balance=0؛ Client باید `member_id` پاسخ و هر ردیف را با نشست تطبیق دهد و مانده را از همان ledger response نمایش دهد.
- وضعیت: M83 backend integration **2 passed**, full backend **812 passed / 2 skipped**؛ route guard و freshness سبز، routes **119**؛ Studio **219/9** + API coverage و build؛ Dart static **61/0**. Flutter widget tests افزوده‌اند اما Flutter/Dart/Java/Android SDK نیست و runtime اجرا نشده؛ M83 از نظر Client `UNKNOWN` است.

## R-031 (M97) — تاریخچهٔ مهاجرت، parity دو مسیر ساخت DB و مانور backup/restore

- تست‌ها: `mp-app/backend/tests/integration/test_m97_migrations_and_backup.py` (۵ تست)، همراه `test_m47_migration_drift.py` و `test_backup_drill.py`.
- رگرسیون‌ها: `alembic upgrade head` و `Base.metadata.create_all` باید schema یکسان بدهند (جدول، ستون+nullable، ایندکس دستی؛ `sqlite_autoindex_*` خارج)؛ تاریخچه یک head، بدون revision تکراری/یتیم/parent گم‌شده و بدون فایل بیرون گراف؛ DB قدیمی با `stamp head` baseline می‌شود و بعد `check` صفر drift؛ `verify` آرشیو دست‌کاری‌شده را پیش از هر نوشتن رد می‌کند؛ `restore --extras-to` فایل‌های زنده (`registry.json`, `design-tokens.json`) را بازنویسی نمی‌کند.
- وضعیت: **36 passed** (M97 + backup drill + M47 + infra + production ops)، Ruff check/format سبز، `bandit -ll` بدون یافته، `docs_gate.py` سبز (7 فایل / 99 لینک / 3 Mermaid). کل backend suite از ریشه: 861 passed / 1 failed — آن یک شکست `test_monitoring::test_alert_rules_cover_slo_and_down` است که مسیر YAML را نسبت به cwd باز می‌کند و از `mp-app/backend` سبز است (۱۰ passed). اجرای واقعی Postgres/DB تولید و Flutter در این sandbox ممکن نیست.

## R-032 (M90) — رسید سفارش عضو: فقط‌خواندنی، بی‌نشت، بی‌جعل مبلغ

- تست‌ها: `mp-app/client/test/shop_orders_receipt_test.dart` (۷ تست)؛ مصرف مسیر در `mp-app/studio/tests/apiCoverage.test.ts`.
- رگرسیون‌ها: رسید فقط با `GET /shop/orders/{id}/receipt` خوانده شود و هیچ `POST`/`PATCH` با مبلغ از جریان رسید نرود؛ پاسخ با `order_id` یا `member_id` نامطابق نمایش داده نشود؛ `lines` غیرلیست/مبلغ غیر `num` → خطای retry؛ اگر `items_total_rial` ≠ `total_rial` هر دو نمایش داده شوند و یادداشت اختلاف بیاید؛ status ناشناخته به «تأییدشده» ترجمه نشود؛ empty/error/retry و رقم فارسی (نه لاتین) در مبلغ‌ها.
- وضعیت: Dart static gate **۶۸ فایل / ۰ یافته**؛ `apiCoverage` **4 passed**؛ Studio **219 passed / 9 skipped** + build. Flutter analyzer/widget test در sandbox اجرا نشد (SDK نیست) → برای Client runtime `UNKNOWN` تا `client-flutter` CI.

## R-033 (M98) — پالس لمسی و کاهش حرکت

- تست‌ها: `mp-app/client/test/motion_haptics_test.dart`، `mp-app/client/test/haptics_recorder.dart`، افزوده‌شده به `set_feedback_sheet_test.dart` و `classes_cancel_test.dart`.
- رگرسیون‌ها: `disableAnimations=true` → `MpMotion.dur` صفر و `target` صفر (و نبودِ MediaQuery → fallback امن)؛ `SystemMpHaptics(enabled: true)` سه فراخوانی روی `SystemChannels.platform` می‌فرستد با آرگومان‌های distinguishable و `enabled: false` صفر فراخوانی؛ ثبت موفق بازخورد = `success` و نه `warning`، ارسال ناموفق = `warning` و نه `success`، و «تکرار خالی → هیچ ارسالی، هیچ پالسی»؛ رزرو/لغو موفق کلاس = یک `success`.
- وضعیت: Dart static gate **۷۲ فایل / ۰ یافته**؛ هیچ dependency تازه‌ای اضافه نشد؛ behavior واقعی روی دستگاه (شدت/تأخیر) سنجیده نشده و Flutter test محلی اجرا نشده → `UNKNOWN` تا CI.

## R-034 (M90/M98) — شکست‌هایی که فقط `flutter test` واقعی می‌گیرد

- تست‌ها: `mp-app/client/test/motion_haptics_test.dart`، `mp-app/client/test/set_feedback_sheet_test.dart`، `mp-app/client/test/shop_orders_receipt_test.dart`.
- رگرسیون‌ها: (۱) فرم ثبت بازخورد باید بدون وابستگی به پاسخ کانال پلتفرم به‌روز شود — «اعمال شد» باید حتی وقتی `HapticFeedback` هیچ‌وقت reply نمی‌دهد روی صفحه بیاید (پالس `void`/fire-and-forget)؛ (۲) `SystemMpHaptics` روی `TargetPlatform.android` دقیقاً سه فراخوانی روی `SystemChannels.platform` می‌فرستد و `enabled: false` صفر تا؛ (۳) متن‌های رسید با همان قالب رندرشده تطبیق داده شوند (`… ریال × ۲`) و ردیف‌های جمع با `find.text` (نه textContaining) سنجیده شوند؛ (۴) `items_total_rial` غیرعددی → پیام «جمع اقلام رسید نامعتبر است» با گزینهٔ تلاش دوباره، نه صفحهٔ خطای build؛ (۵) `rial(5000000.0)` → `۵٬۰۰۰٬۰۰۰ ریال` (بی‌`.۰`).
- وضعیت: پنج مورد از شکست‌های run `44293699567` بود که در `484fcd8` رفع شدند و **run `44295081645` تأییدشان کرد: 154 passed / 2 failed، و هر دو شکستِ باقی‌مانده فقط تست messenger بود** (نه M90). آن دو با حذف `pumpEventQueue()` در `c672737` و در `41ae143` با pin کردن target platform اصلاح شدند؛ سبز شدن کامل از `client-flutter` روی `c672737` خوانده می‌شود (قبل از آن `UNKNOWN`).

## R-035 (M107) — گیت فایل‌محور نباید به cwd وابسته باشد

- تست‌ها: `mp-app/backend/tests/integration/test_monitoring.py::test_alert_rules_cover_slo_and_down` (همان تست، از دو cwd اجرا شد).
- رگرسیون: هر گیتی که فایلِ مخزن را می‌خواند باید مسیر را از `Path(__file__)` بگیرد؛ `Path("../infra/…")` یعنی «این تست فقط اگر از `mp-app/backend` اجراش کنی معنی دارد» — و نتیجه‌اش یک شکستِ بی‌ربط به کد است که خواننده را از کل گیت بی‌اعتماد می‌کند (شاهد تاریخی: 861 passed / **1 failed** از ریشه در برابر 867 از زیرپوشه).
- وضعیت: **رفع شد و سبز از هر دو cwd: 873 passed / 1 skipped** (۲۰۲۶-۱۱-۱۸). `grep -rn 'Path("../' mp-app/backend` حالا صفر مورد دارد.

## R-036 (M108) — چیدنِ گیت‌ها در CI و شاهدِ خواندنی

- تست‌ها: خودِ جاب `client-pinned` (پین، analyze، test+coverage، apk debug)؛ `pin check` با پارس `.devcontainer/Dockerfile` — اگر کسی یکی از دو پین را عوض کند و دیگری را نه، جاب **فیل** می‌شود (نه سبزِ بی‌معنی).
- رگرسیون‌ها: (۱) هیچ گیت تازهای قبل از گیت‌های شاهدچین قرار نگیرد (`bash -e` + skip زنجیره‌ای؛ شاهد: run `44322049209`)؛ (۲) هر گیتِ تازه‌ای که بدهیِ کهنه دارد، با شمارشِ ثبت‌شده در annotation شروع شود تا عدد گم نشود («۶۵ فایل unformatted»)؛ (۳) خروجیِ گیت باید از API خواندنی باشد (`::notice`)، نه فقط لاگ؛ (۴) بیلد اندروید در CI فقط `--debug` و بدون keystore.
- وضعیت: همه روی `2ac6ecc` سبز؛ M109 (فرمت ۶۵ فایل) باز است و پس از آن گیت format کشنده می‌شود.

## R-037 (M109) — commit مکانیکی در CI: چه چیزی باید رد شود

- گیت‌ها: `client-pinned` → «dart format gate (M109 — کشنده)» (`dart format --output=none --set-exit-if-changed lib test tools` بدون `|| echo`)؛ `client-format-fix.yml` → «Stage only tracked .dart modifications» (هر چیزی غیر از `M *.dart` در staged set = fail با `::error`) و «Prove the staged diff changes nothing but layout» (مقایسهٔ `git show HEAD:path` با `git show :path`، با و بدون کاما).
- رگرسیون‌ها: (۱) `git add -A` در هر workflow که پیش‌تر `flutter pub get`/`flutter test --coverage` اجرا کرده **ممنوع** — `pubspec.lock`، `coverage/lcov.info` و بلوک `analyzer: exclude:` که flutter در `analysis_options.yaml` تزریق می‌کند را می‌کشد؛ (۲) proof نباید پیش از گام‌های ابزار اجرا شود؛ (۳) `gh pr create` در CI شکست‌پذیر است (preflight‌های کاربر-محورش با job token مجاز نیستند) — PR را با `gh api -X POST /repos/{}/{}/pulls` بساز؛ و حدسِ اولِ من («نبودِ `metadata: read`») **غلط** بود: آن کلید در `permissions:` مجاز نیست و اضافه‌کردنش کل workflow را بی‌اعتبار می‌کند (run 44349667465: «failed to parse workflow: Unexpected value 'metadata'»، ۰ job — نشانهٔ «۰ job + name=path» یعنی فایل parse نشد، نه اینکه گامی شکست خورد؛ و لاگ jobهای این مخزن از API خالی است، پس خطا را با `::error` منتشر کن)؛ (۴) workflow تازه تا یک‌بار اجرا نشدن dispatch-پذیر نیست (bootstrap با push به همان فایل؛ `main` این مخزن فقط README.md دارد).
- وضعیت: گیتِ فرمت از `cf0ef2c`/`65bbb5e` کشنده است؛ هر push با کدِ فرمت‌نشده روی `mp-app/client` قرمز می‌شود. `flutter` هنوز `analysis_options.yaml` را بازنویسی می‌کند و آن تغییر commit نشده است — اگر کسی روزی آن را commit کند، شاهدِ R-037(۱) باید بگوید «این فقط فرمت نبود»، و هست.

## R-038 (M109) — `dart format` یک ابزارِ **زمینه‌گرا** است

- قاعده: هر گیت/فیکسرِ فرمت باید `flutter pub get` را **پیش از** `dart format` اجرا کند، و هر دو (گیت و fixer) باید همین ترتیب را داشته باشند — وگرنه دو «راستی» متفاوت در repo داریم. نشانهٔ نقض: گیت روی درختی قرمز می‌شود که fixer همین حالا فرمت کرده (run `44350273742`: ۵۳ فایل).
- چکِ محلیِ «فقط چیدمان» روی blobهای staged: `git show HEAD:path` در برابر `git show :path`، با حذف whitespace؛ کاماها به‌عنوان دستهٔ جدا شمرده شوند (tall style کاما جابه‌جا می‌کند؛ short style نه — پس `comma-moved` خودش یک سنسورِ سبک است: PR #1 → ۶۵، PR #2 → ۰).
- رگرسیون‌ها: (۱) جابه‌جاکردنِ گیتِ فرمت به **پیش از** `pub get` یا به پیش از analyze/test/apk ممنوع؛ (۲) `git add -A` در workflow فرمت ممنوع (R-037)؛ (۳) برای ساختن PR در CI، سیاست مخزن را چک کن: `POST /pulls` با job token بدون «Allow GitHub Actions to create and approve pull requests» 403 می‌دهد — شکستِ PR نباید گام را فیل کند اگر شاخه و شواهدش منتشر شده‌اند.
- وضعیت: پس از PR #2، `dart format --set-exit-if-changed` روی درختِ resolve‌شده صفر است و گیت کشنده باقی می‌ماند.
- قاعدهٔ اثباتِ layout: whitespace آزاد؛ کاما تنها «درست پیش از `)]}>`» (افزودن یا حذف). طبقه‌بند در `client-format-fix.yml` همین را روی `git show HEAD:path` در برابر `git show :path` می‌سنجد و ۹ حالت آزمایش دارد (جابه‌جایی آرگومان و متن افزوده/کاسته باید `semantic` بدهند).

## R-039 (M109) — «آیا تغییری هست؟» را به مسیرهایِ خودِ تغییر محدود کن

- قاعده: هر تشخیص «کاری نیست / چیزی برای انتشار هست» باید روی **همان globی** باشد که گام تولید می‌کند (`git status --porcelain -- '*.dart'`، `git diff --cached --name-only`) — نه `git status` خام.
- چرا: `flutter pub get`/`flutter analyze` خودشان `analysis_options.yaml` را دست‌کاری می‌کنند، پس درخت همیشه کثیف است؛ در run `44353087941` روی **درختِ کاملاً فرمت‌شده** گارد «nothing to do» فعال نشد، workflow تا `git commit` پیش رفت و با «nothing added to commit» فیل شد (proof همان‌جا `staged=0` را درست گزارش کرده بود — عدد درست، نتیجهٔ اشتباه).
- هم‌جنسِ R-037 (ممنوعیت `git add -A`): هر دو از یک ریشه‌اند — ابزارِ Flutter در محیطِ کار فایل می‌گذارد، پس هر سنجشِ «تمیزی» باید scoped باشد.

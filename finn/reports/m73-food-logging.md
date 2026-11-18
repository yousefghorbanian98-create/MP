# M73 — ثبت غذای روزانهٔ عضو ایرانی

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — مسیر backend و داده/محاسبات در تست محلی سبز شد؛ Client widget test و Flutter analyze/build به‌علت نبودن Flutter/Dart SDK اجرا نشدند. `PASS` ادعا نمی‌شود.
- دامنه: مصرف APIهای nutrition موجود، کاتالوگ ایرانی موجود و گیت member؛ بدون کاتالوگ خارجی/دادهٔ جدید/مهاجرت.

## Baseline و شکاف کشف‌شده

- Client صفحهٔ برنامهٔ تغذیه را داشت، اما food search/log/day-summary را مصرف نمی‌کرد.
- Backend endpointهای موجود `GET /nutrition/foods`, `POST /nutrition/food-logs` و `GET /nutrition/food-logs/member/{member_id}/daily` را دارد. `log_food` و گزارش روزانه ownership را با `ensure_member_scope` بررسی می‌کنند.
- RBAC برای نقش `member` فقط `GET /api/v1/nutrition/*` را مجاز می‌کرد؛ درخواست ثبت وعدهٔ خود عضو `403` می‌گرفت. تست جدید پیش از تغییر policy همین 403 را ثبت کرد.
- دادهٔ موجود در `mp-app/backend/data/food/iranian_foods.js` منبع `soooolag/food-finder` و مجوز MIT را در سربرگ ثبت می‌کند؛ اسکریپت importer نیز `SOURCE_LICENSE='MIT'` و external ID قابل‌ردیابی دارد. از فایل جاری 305 نام یکتا parse می‌شود. ردیف‌های استفاده‌شده دستهٔ «غذای ایرانی» دارند:
  - قورمه سبزی: 180 kcal، پروتئین 12 g و کربوهیدرات 8 g در 100 g.
  - قیمه: 165 kcal، پروتئین 10 g و کربوهیدرات 12 g در 100 g.
  - آش رشته: 150 kcal، پروتئین 8 g و کربوهیدرات 25 g در 100 g.
- کاتالوگ upstream چربی صریح ندارد؛ importer آن را از رابطهٔ آتووتر برآورد می‌کند. UI این محدودیت را آشکار می‌کند و چربی دفتر روز را نشان نمی‌دهد؛ مقدار ورودی کاربر وزن واقعی به گرم است، نه portion ساختگی.

## تغییرها

- `mp-app/client/lib/core/app_state.dart`: providerهای search و daily-summary برای API موجود؛ query فارسی encode می‌شود؛ پاسخ غیرلیستی/ردیف نامعتبر خطاست، نه غذای خالی.
- `mp-app/client/lib/features/nutrition/nutrition_page.dart`: جست‌وجو و انتخاب از کاتالوگ واقعی، مقدار گرم (پذیرش رقم فارسی/عربی/لاتین)، انتخاب وعده، POST به endpoint موجود، سپس invalidate و خواندن مجدد جمع روز. «ثبت‌نشده» صفرمصرف تعبیر نمی‌شود؛ خطا نیز عدد صفر نمی‌سازد. نتیجه‌ها و هشدار وزن خشک/خام فارسی‌اند.
- `mp-app/backend/security/rbac.py`: فقط `POST /api/v1/nutrition/food-logs` به نقش member افزوده شد؛ بررسی `member_id` همچنان در service انجام می‌شود. هیچ POST برنامه/تأیید مربی یا نوشتن کاتالوگ باز نشده است.
- `mp-app/backend/tests/unit/test_food_catalog_import.py`: آزمون فایل موجود، سه غذای ایرانی، دسته، license، منشأ و مقادیر پایه.
- `mp-app/backend/tests/integration/test_m49_food_logging.py`: تست member self-log و totals؛ ثبت سه غذای بالا با 150/200/250 g و totalهای 975 kcal، 58 g پروتئین، 98.5 g کربوهیدرات و 38.8 g چربی محاسباتی؛ تست مالکیت cross-member و ممنوع‌ماندن create/approve برنامه.
- `mp-app/client/test/nutrition_food_log_test.dart`: widget path و parser رقم فارسی نوشته شد؛ اجرای widget آن در این محیط ممکن نبود.
- هیچ غذای جدیدی به dataset اضافه نشد؛ CORGIS، غذا/دستور غیرایرانی جدید، dependency، schema یا migration اضافه نشد.

## شواهد اجراشده

- تست regression پیش از policy: `test_member_can_log_food_for_self` → **قرمز: 403** با پیام نقش `member` برای POST nutrition food-logs مجاز نیست.
- پس از اصلاح:
  `PYTHONPATH=/tmp/mp-backend-test-deps:mp-app/backend python3 -m pytest -q mp-app/backend/tests/unit/test_food_catalog_import.py mp-app/backend/tests/integration/test_m49_food_logging.py`
  → **25 passed**. شامل تست سه غذای ایرانی، مقدار/جمع روزانه، member self-log و رد مالکیت دیگر عضو.
- `ruff check` روی سه فایل Python تغییرکرده → **All checks passed**.
- `python3 -m py_compile` روی همان فایل‌های backend → موفق.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **44 فایل Dart، 0 یافته**؛ این گیت نحوی/الگوی ایستا است، نه analyzer یا اجرای Flutter.
- نصب موقت test dependencies فقط زیر `/tmp` انجام شد؛ هیچ package/lockfile پروژه تغییر نکرد.

## گیت اجرا‌نشده و محدودیت

- `flutter test test/nutrition_food_log_test.dart`، `flutter analyze` و Client build اجرا نشدند؛ `flutter` و `dart` در PATH یا مسیرهای متعارف سیستم پیدا نشدند. widget test نوشته‌شده runtime evidence محسوب نمی‌شود.
- Pytest خروجی 25 تست را سبز کرد، با دو هشدار محیط نصب موقت: Starlette deprecation برای `httpx`/TestClient و pytest config ناشناختهٔ `asyncio_mode` (pytest-asyncio در target نصب نبود). این‌ها شکست تست نبودند.
- اعداد منبع، مقدارهای گزارش‌شدهٔ خود کاتالوگ‌اند، نه برچسب آزمایشگاهی/توصیهٔ بالینی؛ چربی به‌طور خاص اندازه‌گیری مستقیم نیست.
- فقط SQLite موقت و دادهٔ مصنوعی؛ بدون DB تولید، دادهٔ واقعی، push، CI یا پرداخت.

## تصمیم و بازگشت

- D-035: اجازهٔ member فقط برای endpoint ثبت غذای عضو، نه wildcard نوشتن در nutrition؛ owner check واقعی در service حفظ شود. از کاتالوگ MIT موجود استفاده شود؛ کاربر مقدار گرم می‌دهد؛ مقادیر per-100g از API می‌آیند؛ چربیِ محاسباتی در UI نمایش داده نشود.
- برگشت‌پذیری: policy line، providers/UI/tests مستقل و قابل بازگردانی‌اند؛ schema، DB و endpoint contract تغییر نکردند.
- M73 در نقشه `UNKNOWN` می‌ماند تا widget test/analyzer/build اجرا شوند؛ loop مستقل بعدی M74 است.

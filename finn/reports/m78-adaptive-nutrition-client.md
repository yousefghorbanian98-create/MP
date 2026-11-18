# M78 — تغذیهٔ تطبیقی در Client

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — backend مالکیت/RBAC و static Dart gate سبز؛ Flutter widget test/analyze/build اجرا نشده.
- معیار: TDEE و delta از API واقعی؛ دادهٔ ناکافی صادقانه؛ بدون توصیهٔ پزشکی.

## Baseline و دسترسی وزن

- API تطبیقی موجود `/nutrition/member/{member_id}/adaptive` سه منبع واقعی دارد: وزن، روزهای ثبت غذا و آخرین برنامهٔ تغذیهٔ approved؛ موتور برای ورودی ناکافی `tdee_kcal=null` می‌دهد و action را `none` می‌کند.
- endpoint موجود `/nutrition/weight-logs` و service `ensure_member_scope` داشت، ولی RBAC برای member مجوز POST نداشت. integration test پیش از fix ثبت وزن خود عضو را با **403** بازتولید کرد.
- برای اینکه عضو بتواند یکی از ورودی‌های واقعی برآورد را با API موجود وارد کند، فقط مجوز دقیق `POST /nutrition/weight-logs` به member اضافه شد؛ no wildcard و هیچ دسترسی نوشتن برنامه/کاتالوگ/غذاهای دیگر باز نشد. `ensure_member_scope` مرز self-only است.

## تغییرها

- `core/app_state.dart`: `adaptiveNutritionProvider` member ID را از نشست می‌گیرد و report/estimate/trend/counts/suggestion و owner را اعتبارسنجی می‌کند؛ خطا یا shape خراب به عدد ۰/دادهٔ ناکافی تبدیل نمی‌شود.
- `features/nutrition/adaptive_nutrition_card.dart`: TDEE، روند kg/week، میانگین مصرف، هدف فعلی، confidence و suggestion/delta/target فقط از پاسخ API؛ count وزن و روزهای غذا، reason/notes/assumptions. اگر TDEE یا target نامعلوم است، همان را نشان می‌دهد.
- فرم ثبت وزن امروز، رقم فارسی/عربی و بازهٔ قرارداد ۲۰–۴۰۰ kg؛ `POST /nutrition/weight-logs` با member نشست و تاریخ امروز local. response واقعی بررسی می‌شود؛ پس از موفقیت provider تازه‌خوانی می‌شود. ثبت تکراری امروز طبق service همان رکورد روز را به‌روزرسانی می‌کند.
- card به NutritionPage افزوده شد. خطای read جدا از insufficient data، retry و status ثبت جدا هستند.
- disclaimer: تخمین انرژی از روند وزن/غذاست و توصیهٔ درمانی یا رژیم پزشکی نیست؛ هیچ هدف کالری یا TDEE سمت Client محاسبه نمی‌شود.
- `test_m78_adaptive_nutrition_client.py` self write، cross-member 403، شمار وزن در گزارش، TDEE نامعلوم و پیشنهاد none را می‌آزماید؛ RBAC matrix مجوز دقیق weight-log و رد POST برنامه را قفل می‌کند.
- `adaptive_nutrition_test.dart` TDEE/تغییر هدف API، دادهٔ ناکافی، ثبت وزن با رقم فارسی + member/date body + refetch، خطا/retry و parser range را می‌آزماید. fake response M73 نیز برای report جدید معتبر شد.
- API/schema/service/DB/migration/dependency جدیدی اضافه نشد؛ تنها policy دقیق و UI/fixture.

## شواهد

- پیش از تغییر policy: test self weight logging → **403**.
- پس از fix:
  `PYTHONPATH=/tmp/mp-backend-test-deps:mp-app/backend python3 -m pytest -q mp-app/backend/tests/integration/test_m78_adaptive_nutrition_client.py mp-app/backend/tests/integration/test_m49_adaptive_nutrition.py mp-app/backend/tests/regression/test_rbac.py mp-app/backend/tests/unit/test_adaptive_nutrition.py`
  → **74 passed**؛ شامل self/cross-member write، adaptive report، RBAC و موتور.
- `python3 -m py_compile` روی RBAC/testها موفق؛ Ruff **All checks passed**.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **53 فایل Dart، 0 یافته**.
- محیط Flutter/Dart ندارد؛ `flutter test`, `flutter analyze` و build اجرا نشده‌اند. static gate جای اجرا/type analysis را نمی‌گیرد؛ M78 `UNKNOWN` است.
- Pytest با هشدارهای موقت Starlette/httpx، `asyncio_mode` ناشناخته، و یک هشدار 422 deprecated در تست قبلی اجرا شد؛ suite سبز.

## Rollback و اثر

- rollback شامل یک policy دقیق، RBAC regression/integration، provider/card/page و تست‌های Client است. endpoint/service/DB/migration/dependency تغییر نکرده.
- حذف policy self logging را دوباره 403 می‌کند؛ cross-member همچنان با service guard بسته است. UI rollback، مصرف read report و فرم وزن را برمی‌گرداند.

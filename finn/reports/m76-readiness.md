# M76 — آمادگی/خستگی در Client

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — کد Client و widget test نوشته و static-parse شده؛ Flutter test/analyze/build اجرا نشده‌اند.
- معیار: readiness از API واقعی MP، توضیح و توصیه به‌عنوان برآورد، loading/empty/error/retry و بدون عدد mock.

## پیاده‌سازی

- مصرف endpoint موجود `GET /api/v1/programs/member/{member_id}/readiness`; router سرور از قبل `ensure_member_scope` اجرا می‌کرد و backend readiness را از set feedback واقعی می‌ساخت.
- `readinessProvider`: member ID از نشست، owner ID و schema مهم گزارش، score، band/recommendation، signals و missing signals اعتبارسنجی می‌شوند. خطا/payload خراب به score صفر یا `readiness=null` تبدیل نمی‌شود.
- `ReadinessCard` در صفحهٔ Today: score و band از پاسخ، توصیه و دلیل موتور، سیگنال‌های معلوم/نامعلوم، تعداد بازخورد و ست‌های ۷روزه. حالت بارگیری، داده ناکافی/بدون برنامه، خطای API و retry جدا هستند.
- متن صریح: «این برآورد از بازخورد تمرین ثبت‌شده و قواعد MP می‌آید؛ تشخیص پزشکی نیست.» هیچ score، band یا توصیهٔ محلی ساخته نمی‌شود.
- پس از پاسخ موفق ثبت بازخورد ست، `readinessProvider` invalidate می‌شود تا خواندن بعدی وضعیت تازه را نشان دهد.
- `readiness_card_test.dart`: loading→گزارش دارای 68.4/100، سیگنال RIR نامعلوم و توصیه؛ empty (`readiness=null`) بدون امتیاز ساختگی؛ error/retry.
- فقط Client تغییر کرد؛ endpoint، backend model/service، schema، DB، dependency و medical logic تغییر نکرد.

## شواهد

- `PYTHONPATH=/tmp/mp-backend-test-deps:mp-app/backend python3 -m pytest -q mp-app/backend/tests/unit/test_readiness.py mp-app/backend/tests/integration/test_m48_feedback_applied.py -k readiness`
  → **22 passed, 7 deselected** (فیلتر `-k readiness`؛ suite کامل این فایل‌ها در این نوبت اجرا نشد).
- `py_compile` و Ruff روی router/service موجود → موفق/پاک؛ کد backend تغییری نکرد.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **49 فایل Dart، 0 یافته**.
- Flutter و Dart executable محلی نیست؛ `flutter test`, `flutter analyze` و build اجرا نشده‌اند. Static gate اجرای widget و بررسی type را جایگزین نمی‌کند.
- هشدارهای pytest ابزار موقت: Starlette/TestClient و گزینهٔ ناشناختهٔ `asyncio_mode`؛ ۲۲ تست شکستی نداشتند.

## Rollback

- فقط `app_state.dart`, `features/today/readiness_card.dart`, `today_page.dart`, `set_feedback_sheet.dart` و تست widget؛ migration/backend تغییر نکرده.
- حذف invalidation صرفاً تازگی بعد از feedback را می‌برد؛ حذف provider/card رفتار M76 را برمی‌گرداند. M76 `UNKNOWN` می‌ماند تا اجرای Flutter در محیط دارای SDK.

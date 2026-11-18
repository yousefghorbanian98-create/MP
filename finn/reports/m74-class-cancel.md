# M74 — لغو member-scoped رزرو کلاس

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — backend integration و گیت ایستای Dart پاک‌اند؛ Client widget test و Flutter analyzer/build اجرا نشدند.
- معیار: لغو رزرو خود عضو، تازه‌شدن ظرفیت، duplicate cancellation و مالکیت.

## Baseline و باگ‌های بازتولیدشده

- Flutter صفحهٔ کلاس را فهرست/رزرو می‌کرد، اما حالت رزرو خود عضو را نمی‌دید و مسیر لغو نداشت.
- `GET /classes` ظرفیت را می‌داد، اما به هر class مورد رزرو همان عضو را اضافه نمی‌کرد؛ Client راه مطمئنی برای ارائهٔ action لغو نداشت.
- تست pre-fix با دو عضو مصنوعی: member B با ارسال `member_id` عضو A، رزرو A را لغو کرد و **200** گرفت. کنترل مالکیت در service وجود نداشت.
- در همان قرارداد `BookIn`، member B می‌توانست برای A نیز `/classes/book` بزند؛ تست pre-fix آن را هم با **200** بازتولید کرد. این باگ در endpoint مجاور و همان مرز مالکیت بود، بنابراین در همین اصلاحِ service-level بسته شد.

## تغییرها

- `modules/classes/service.py`: `book` و `cancel` حالا `ensure_member_scope` را صدا می‌زنند؛ staff که این check برایشان noop است رفتار قبلی را نگه می‌دارند. لغو رزرو تکراری همچنان خطای 404 می‌دهد.
- `modules/classes/router.py`: `CurrentUser` به service می‌رسد. در `GET /classes`، فقط برای role `member`، وضعیت رزرو همان member افزوده می‌شود؛ شناسه از رابطهٔ user→member گرفته می‌شود، نه از پارامتر کاربر.
- `list_classes` وضعیت confirmed/waitlisted عضو را از ردیف‌های خودش می‌سازد. لغو confirmed، نفر اول waitlist را به confirmed ارتقا می‌دهد؛ response همچنان ظرفیت/شمارش را تازه می‌کند.
- `client/lib/features/classes/classes_page.dart`: رزروهای confirmed/waitlisted دکمهٔ لغو می‌گیرند؛ member_id از نشست می‌آید؛ درخواست هم‌کلاس هم‌زمان قفل می‌شود؛ موفقیت/خطا کلاس‌ها را از API invalidate/refetch می‌کند.
- `test_m74_class_cancel.py`: cross-member cancel و booking، لغو خود عضو، لغو تکراری، ارتقای waitlist و ظرفیت/status تازه.
- `client/test/classes_cancel_test.dart`: widget flow لغو و refetch با fake API نوشته شد.
- migration/schema/API route تازه یا dependency اضافه نشد.

## شواهد اجراشده

- قبل از fix، cross-member cancel → **200** و cross-member book → **200** (دو regression red واقعی).
- پس از fix:
  `PYTHONPATH=/tmp/mp-backend-test-deps:mp-app/backend python3 -m pytest -q mp-app/backend/tests/integration/test_m74_class_cancel.py mp-app/backend/tests/integration/test_classes_finance.py mp-app/backend/tests/regression/test_rbac.py`
  → **46 passed**؛ شامل چهار تست جدید M74 و تست‌های ظرفیت/صف انتظار و RBAC.
- `python3 -m py_compile` برای backend router/service/test → موفق.
- `ruff check` روی همان backend paths → **All checks passed**.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **45 فایل Dart، 0 یافته**.

## محدودیت و گیت اجرا‌نشده

- `flutter test test/classes_cancel_test.dart`, `flutter analyze` و Client build اجرا نشدند؛ Flutter/Dart SDK موجود نیست. گیت Tree-sitter فقط syntax/pattern را بررسی می‌کند و test widget را اجرا نمی‌کند.
- Pytest سبز شد با دو هشدار ابزار موقت: Starlette/TestClient دربارهٔ httpx deprecation و pytest ناشناخته‌بودن `asyncio_mode` (pytest-asyncio نصب نبود).
- فقط SQLite موقت و اعضای مصنوعی؛ نه DB تولید، نه دادهٔ واقعی، نه CI/push.

## تصمیم و rollback

- D-036: لیست کلاس member می‌تواند status رزرو همان عضو را برگرداند تا UI عمل‌پذیر باشد؛ service مرز مالکیت را برای book و cancel اعمال می‌کند. اصلاح book همراه cancel انجام شد چون تست همان الگوی سوءاستفاده را در endpoint مجاور با 200 ثابت کرد.
- اثر بازگشت محدود به route/service، Client UI و تست‌هاست؛ DB/schema تغییر نکرد. بازگرداندن hunks یادشده رفتار قبلی را برمی‌گرداند و این آسیب‌پذیری‌ها را باز می‌کند.
- M74 در نقشه `UNKNOWN` می‌ماند تا Flutter widget/analyzer/build اجرا شوند؛ loop مستقل بعدی M75 است.

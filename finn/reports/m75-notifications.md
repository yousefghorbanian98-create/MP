# M75 — inbox اعلان عضو، unread count و mark-as-read

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — API/backend و static Dart gate سبز؛ Flutter widget test، analyze و build اجرا نشده‌اند.
- دامنهٔ معیار: سه اعلان نمونه، حالت خالی/خطا، unread count، mark-read و ownership؛ استفاده از APIهای موجود، بدون push/local scheduler جدید.

## Baseline / بازتولید

- Backend API موجود: `GET /api/v1/notifications/member/{member_id}` و `POST /api/v1/notifications/{notification_id}/read`.
- تست‌های pre-fix با دو عضو مصنوعی ثابت کردند عضو غیرمالک می‌توانست لیست عضو دیگر را بخواند (**200**) و اعلان او را read کند (**200**). router فقط RBAC مسیر/متد را داشت؛ service مالکیت را اعمال نمی‌کرد.
- Flutter عضو inbox، unread count و action برای read نداشت.

## تغییرها

- `modules/notification/router.py`: `CurrentUser` را به list/read service می‌فرستد.
- `modules/notification/service.py`: `ensure_member_scope` برای فهرست عضو و رکورد notification در mark-read؛ staff behavior حفظ می‌شود. رکورد ناموجود همچنان 404 است و رکورد دیگران برای member، 403 می‌دهد.
- `client/lib/core/app_state.dart`: `myNotificationsProvider` هویت را از نشست می‌گیرد، payload list/شناسه/عنوان/زمان را اعتبارسنجی می‌کند و خطای API یا payload خراب را به inbox خالی تبدیل نمی‌کند؛ شمارش unread از `read_at` است.
- `client/lib/features/notifications/notifications_page.dart`: UI فارسی با unread count، خوانده‌شده/نشده، تاریخ جلالی، mark-read، refresh، empty و error/retry.
- `core/router.dart`: مسیر `/notifications`; `home_page.dart`: دکمهٔ زنگ و badge با تعداد unread واقعی.
- widget tests: سه اعلان → mark-read → refetch/count کاهش‌یافته؛ empty؛ error و retry؛ badge خانه.
- backend tests: منع cross-member list/read، جلوگیری از تغییر `read_at` صاحب، سه اعلان unread، mark own read و باقی‌ماندن دو unread.
- API route، schema/model/DB، migration، dependency، push یا scheduler جدید اضافه نشد.

## شواهد اجراشده

- پیش از اصلاح، دو تست ownership هر دو با پاسخ **200** شکست خوردند (انتظار 403).
- پس از اصلاح:
  `PYTHONPATH=/tmp/mp-backend-test-deps:mp-app/backend python3 -m pytest -q mp-app/backend/tests/integration/test_m75_notifications.py mp-app/backend/tests/integration/test_m55_reminders.py mp-app/backend/tests/integration/test_m51_chat.py mp-app/backend/tests/regression/test_rbac.py`
  → **65 passed**؛ شامل M75، reminders/materialization، chat و RBAC.
- `python3 -m py_compile` روی router/service/test → موفق.
- `ruff check` روی همان backend paths → All checks passed.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **47 فایل Dart، 0 یافته**.

## محدودیت و rollback

- `flutter` و `dart` executable در sandbox نیست؛ `flutter test test/notifications_page_test.dart`, home badge test، `flutter analyze` و build اجرا نشدند. Tree-sitter static gate جای اجرای widget و analyzer نیست؛ status را `PASS` نمی‌نامیم.
- Pytest با هشدارهای محیطی Starlette/httpx و `asyncio_mode` اجرا شد؛ یک هشدار deprecated اضافی از تست chat هم دیده شد؛ suite شکست نداشت.
- فقط SQLite موقت و توکن/اعضای synthetic؛ نه DB تولید، دادهٔ عضو واقعی، CI، push یا release.
- Rollback فقط هانک‌های router/service/provider/page/route/home/tests را برمی‌گرداند؛ DB migration ندارد. حذف guard مالکیت دسترسی متقاطع pre-fix را بازمی‌گرداند.
- طبق نقشه، loop بعدی مستقل M76 است؛ M75 تا اجرای واقعی Flutter `UNKNOWN` باقی می‌ماند.

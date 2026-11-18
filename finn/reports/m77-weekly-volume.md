# M77 — حجم هفتگی عضلات در Client

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — داده/API و static gate سبز؛ Flutter widget test/analyze/build اجرا نشده.
- معیار: حجم واقعی عضو، نمودار/ست‌ها در برابر MV/MEV/MAV/MRV، تفکیک برنامه از گزارش، empty/loading/error، عضو درست؛ بدون dependency تازه.

## تغییرها

- استفاده از API موجود `GET /programs/member/{member_id}/volume?level=...`; endpoint از قبل `ensure_member_scope` دارد.
- `volumeProvider` هویت را از نشست می‌گیرد، level را به beginner/intermediate/advanced محدود و member_id، rows، landmarks و suggestion را اعتبارسنجی می‌کند. پاسخ خراب به حجم صفر تبدیل نمی‌شود.
- `VolumeCard` به Today اضافه شد: انتخاب سطح، bar نمودار با band MAV و actual/effective sets؛ status MV/MEV/MAV/MRV؛ مقدار planned در برابر hard sets گزارش‌شده؛ ست سخت/راحت/RIR نامعلوم؛ suggestion هفتهٔ بعد با دلیل و source جدول. اعداد و source از API هستند.
- حالات loading، خطا/retry و نبود برنامه با reason واقعی؛ refresh به API. UI صریح می‌گوید حدود، قاعدهٔ برنامه‌ریزی تمرین‌اند و معادله/تشخیص پزشکی نیستند.
- widget testها: endpoint member/سطح intermediate→beginner، مقدار/منبع/حدها/پیشنهاد، empty و خطا/retry.
- هیچ API، backend، schema، DB یا dependency تغییر نکرد.

## شواهد و محدودیت

- `PYTHONPATH=/tmp/mp-backend-test-deps:mp-app/backend python3 -m pytest -q mp-app/backend/tests/integration/test_m48_volume_api.py mp-app/backend/tests/unit/test_load_attribution.py` → **13 passed**؛ شامل planned-vs-feedback، ownership و attribution.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **51 فایل Dart، 0 یافته**.
- Flutter و Dart executable در sandbox نیست؛ `flutter test test/volume_card_test.dart`, analyzer و build اجرا نشدند. static tree-sitter gate جای type/runtime test نیست، پس M77 `UNKNOWN`.
- Pytest دو هشدار محیطی Starlette/httpx و `asyncio_mode` ناشناخته داشت.

## Rollback

- فقط `core/app_state.dart`, `features/today/volume_card.dart`, `today_page.dart` و Client widget test؛ backend/API/dependency/migration ندارند. حذف UI/provider را برمی‌گرداند؛ endpoint موجود دست‌نخورده می‌ماند.

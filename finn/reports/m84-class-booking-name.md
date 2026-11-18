# M84 — نمایش نام معتبر در جریان رزرو کلاس

- تاریخ: 2026-11-17
- شاخه: `arena/4f336f66-mp`
- وضعیت: **UNKNOWN** — پیاده‌سازی و backend tests پاس شدند؛ Flutter analyzer/widget runtime برای همین تغییر هنوز اجرا نشده است.

## دامنه و تغییر

- پاسخ `POST /classes/book` نام عضو را از رابطهٔ معتبر `Member → User.full_name` می‌خواند؛ فیلد جعلی `member_name` در payload نادیده گرفته می‌شود.
- فهرست کلاس برای عضو فقط نام رزرو فعالِ خودش را با `member_booking_name` برمی‌گرداند. پاسخ staff شامل نام عضوها نیست؛ رزروهای دیگران در feed عضو نشت نمی‌کند.
- Client در پیام تأیید رزرو و وضعیت confirmed/waitlisted، نامی را نمایش می‌دهد که API برگردانده است؛ در صورت نبودن نام، متن عمومی حفظ می‌شود.
- ظرفیت/انتظار، شناسهٔ رزرو و سیاست مالکیت تغییر نکردند؛ migration یا endpoint تازه لازم نیست.

## شاهد

- `ruff check .` و `ruff format --check .` برای کل backend: سبز.
- اجرای هدفمند `test_m84_class_booking_name.py`, `test_m74_class_cancel.py`, `test_classes_finance.py` و `test_m57_sync.py`: **20 passed**, دو هشدار deprecation.
- اجرای full backend معادل coverage gate در CI: **853 passed, 2 skipped**, پوشش **86.30%** (حد لازم 70%); 29 هشدار deprecation/runtime در مجموعه.
- تست‌های تازه: نام از DB در پاسخ member و staff؛ payload دستکاری‌شده نام را عوض نمی‌کند؛ member نمی‌تواند برای دیگری رزرو کند؛ نام رزرو در feed فقط برای owner است؛ ظرفیت پر، waitlist و عدم افشای نام به staff aggregate.
- Widget test در `mp-app/client/test/classes_cancel_test.dart` confirmation و label را بررسی می‌کند. CI `44202586219` full suite را با **101 passed / 13 failed** اجرا کرد؛ CI `44247416109` نیز 13 failures داشت. Annotationهای آن run نام 9 failure را در bodycomp/session/volume/adaptive-nutrition/check-in tests نشان دادند، اما چهار مورد به‌علت annotation cap حذف شدند؛ `classes_cancel_test.dart` در نام‌های نمایان نبود، پس نتیجهٔ مجزای M84 نامعلوم است.
- CI `44194271168` روی commit `6475455` اجرا شد، پیش از M84–M87 implementation؛ پس برای این loop شاهد نیست.
- CI `44198198864` روی commit `b7cd7f1` شامل backend/UI/test M84 بود؛ backend/API jobs پاس شدند، اما analyzer پیش از Flutter tests شکست خورد. علت‌های analyzer و Studio coverage در `0ace8fe` اصلاح شدند؛ CI `44200381791` آن fixها را تأیید کرد، با backend/Studio/live-contract/e2e-api سبز.
- در `44200381791` analyzer روی warning outbox شکست خورد؛ در `44202586219` آن پاس شد ولی full suite **101 passed / 13 failed** داشت. در `44247416109` analyzer نیز پاس شد و helper 13 failures شمرد؛ فقط 9 test names از 5 فایل نمایان شد، چهار نام به‌علت annotation cap جا افتاد. نتیجهٔ مجزای `classes_cancel_test.dart` هنوز نامعلوم، پس M84 `UNKNOWN` می‌ماند. Worktree helper را به یک annotation کامل تغییر می‌دهد؛ assertion values/stack traces چاپ نمی‌شوند. Secret-scan همچنان روی matchهای تاریخی fail است؛ جزئیات redacted در `finn/reports/ci-follow-up-441922-441942.md`.

## بازگشت

تغییرهای همین loop را در `modules/classes/router.py`, `modules/classes/service.py`, `tests/integration/test_m84_class_booking_name.py`, `client/lib/features/classes/classes_page.dart` و `client/test/classes_cancel_test.dart` revert کن. migration، داده یا side effect بیرونی وجود ندارد.

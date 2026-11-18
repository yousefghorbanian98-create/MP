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
- Widget test در `mp-app/client/test/classes_cancel_test.dart` confirmation و label را بررسی می‌کند. Flutter/Dart در sandbox محلی موجود نیست؛ CI `44202586219` full suite را اجرا کرد (**101 passed / 13 failed**) اما annotationها نتیجهٔ مجزای این فایل را نشان نمی‌دهند، پس تا شناسایی تست‌های fail نمی‌توان PASS داد.
- CI `44194271168` روی commit `6475455` اجرا شد، پیش از M84–M87 implementation؛ پس برای این loop شاهد نیست.
- CI `44198198864` روی commit `b7cd7f1` شامل backend/UI/test M84 بود؛ backend/API jobs پاس شدند، اما analyzer پیش از Flutter tests شکست خورد. علت‌های analyzer و Studio coverage در `0ace8fe` اصلاح شدند؛ CI `44200381791` آن fixها را تأیید کرد، با backend/Studio/live-contract/e2e-api سبز.
- در `44200381791` client analyzer روی warning `UNUSED_ELEMENT_PARAMETER` شکست خورد و Flutter tests skip شدند. در CI `44202586219` analyzer پاس شد و full Flutter suite اجرا شد ولی **101 passed / 13 failed**؛ test names در annotations نبودند و artifact/log با EOF دانلود نشد، پس نتیجهٔ test مشخصاً مربوط به M84 قابل‌تأیید نیست و `UNKNOWN` می‌ماند. Worktree instrumentation برای CI بعدی test names/source lines را بدون assertion values ثبت می‌کند. Secret-scan هر دو run به‌دلیل matchهای تاریخی fail مانده؛ جزئیات redacted در `finn/reports/ci-follow-up-441922-441942.md`.

## بازگشت

تغییرهای همین loop را در `modules/classes/router.py`, `modules/classes/service.py`, `tests/integration/test_m84_class_booking_name.py`, `client/lib/features/classes/classes_page.dart` و `client/test/classes_cancel_test.dart` revert کن. migration، داده یا side effect بیرونی وجود ندارد.

# M80 — تاریخچهٔ حضور عضو، self-scoped

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** تا اجرای Flutter widget/analyze gate؛ backend و static Dart gates سبز.

## تغییر پیاده‌سازی

### API و مالکیت

- `GET /api/v1/members/me/checkins?limit=30&offset=0` به router `members` اضافه شد.
- member ID فقط از `user.id` نشست و رکورد `Member` متناظر استخراج می‌شود؛ سرویس فقط `CheckIn.member_id == own_member.id` را query می‌کند. تلاش برای تعیین `member_id` در query این مسیر صریحاً 403 می‌گیرد و مقصد تاریخچه قابل‌انتخاب نیست.
- فقط نقش `member` مجاز است؛ کاربر بدون پروفایل 404 می‌گیرد. دسترسی عضو به `/members/{other_id}` و `/admin/checkins?member_id=...` نیز با 403 رد می‌شود. سقف pagination برابر 100 رکورد در هر درخواست و offset حداکثر 1,000,000 است؛ پاسخ `has_more` می‌دهد.
- جدیدترین رکورد اول است. ورودهای `ok` و `denied` هر دو حفظ می‌شوند؛ پاسخ حداقل فیلدهای لازم برای عضو را دارد و نام عضو، QR token/hash یا رکورد عضو دیگر را برنمی‌گرداند.
- `/api/v1/admin/checkins` دست‌نخورده و member همچنان 403 است.

### Client

- تب سوم «سوابق» به صفحهٔ چک‌این اضافه شد؛ داده از مسیر self-scoped بالا خوانده می‌شود و هیچ شناسهٔ عضو از Client ارسال نمی‌شود.
- ردیف‌ها روش ورود، وضعیت، زمان ورود/خروج و دلیل رد شدن را نشان می‌دهند؛ روش «face» با عبارت شفاف «ثبت از صفحهٔ چهره» نمایش داده می‌شود، نه ادعای تشخیص چهره.
- حالت‌های loading، خطا/retry، تاریخچهٔ خالی و pagination «سوابق قدیمی‌تر» پیاده شدند. پس از چک‌این face، صفحهٔ اول تاریخچه invalidate می‌شود.

## شاهد و محدودیت

- تمرکز M80/ownership/feed/RBAC: **57 passed**؛ کل backend suite با اجرای درست از `mp-app/backend`: **811 passed, 1 skipped** (29 هشدار عمدتاً deprecation/config).
- `ruff check .` و `ruff format --check .` روی کل backend سبز؛ 8 فایل قدیمی فقط format شده‌اند تا گیت کامل سبز شود. `py_compile` روی router/service/test نیز سبز.
- `api/routes.json` با `scripts/export_routes.py` بازتولید شد و 115 مسیر دارد؛ گیت تازگی artifact از این پس سبز است.
- `PYTHONPATH=/tmp/mp-m80-deps python3 mp-app/client/tools/dart_gate.py --include-tests` → **55 فایل Dart، 0 یافته**؛ manifest gate → **1 مانیفست، 0 یافته**.
- جست‌وجو و تلاش دانلود SDK در گزارش `finn/reports/flutter-sdk-provisioning.md` ثبت شده است. archive پایدار Flutter 3.50.0 از mirror منتخب در sandbox با TLS دریافت نشد؛ `flutter` و `dart` نصب نیستند. در نتیجه `flutter analyze`، `flutter test` و Android build اجرا نشده‌اند. Static parser جایگزین runtime نیست؛ M80 همچنان `UNKNOWN` است.
- DB schema، migration، dependency و تجربهٔ کاربر staff تغییر نکردند.

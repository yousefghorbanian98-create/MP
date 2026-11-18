# M72 — نمایش وضعیت و پایان اشتراک عضو

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** — پیاده‌سازی و گیت ایستای Dart بررسی شد، اما Flutter/Dart test و analyzer در sandbox قابل اجرا نبودند. `PASS` ادعا نمی‌شود.
- دامنه از نقشهٔ جاری: وضعیت active/expired/بدون اشتراک، تاریخ پایان واقعی و مرز زمانی؛ فقط endpoint موجود و دادهٔ API.

## Baseline و قرارداد واقعی

- `GET /api/v1/members/{member_id}/memberships` در `mp-app/backend/modules/membership/router.py` تاریخچه را از DB برمی‌گرداند، به `MembershipOut` متصل است و `ensure_member_scope` را اجرا می‌کند.
- `MembershipOut` شامل `status` و `expires_at` است؛ فیلد `days_remaining` ندارد. مدل اشتراک وضعیت‌های `active | expired | cancelled` را مستند می‌کند و `expires_at` از نوع datetime است.
- Provider قبلاً هر پاسخ غیرلیستی را به `[]` تبدیل می‌کرد؛ این می‌توانست پاسخ ناقص/قرارداد شکسته را در UI به «بدون اشتراک» تعبیر کند. بنر روزهای باقی‌مانده می‌ساخت، اما تاریخ تقویمی پایان را نشان نمی‌داد.

## تغییرهای محدود M72

- `mp-app/client/lib/core/membership.dart`: parse timestamp با zone صریح؛ تعبیر timestamp بی‌zone به UTC؛ ورودی نامعتبر/غیررشته‌ای به‌عنوان نامعلوم؛ خلاصه‌سازی active/expired/none/unknown؛ پایان در همان لحظه یا قبل از آن منقضی است؛ شمارش روز با گردکردن رو به بالا؛ نمایش جلالی با رقم فارسی.
- `mp-app/client/lib/core/app_state.dart`: پاسخ history غیرلیستی یا نبود `memberId` خطا می‌شود و به فهرست خالی تبدیل نمی‌شود. endpoint و ownership دست‌نخورده ماندند.
- `mp-app/client/lib/features/home/home_page.dart`: بنر از خلاصهٔ helper استفاده می‌کند؛ active شامل تاریخ جلالی پایان و روزهای باقی‌مانده است؛ expired، none و unknown از هم متمایزند؛ loading/error متن یا عدد ساختگی نمی‌دهند.
- `mp-app/client/test/membership_test.dart`: تست‌های نوشته‌شده برای ۲۳ ساعت، ۲۴ روز، گذشته، لحظهٔ دقیق و یک میکروثانیه پس از مرز، ورودی نامعتبر/غیررشته‌ای، active/expired/none و تبدیل جلالی.
- `mp-app/client/test/home_banner_test.dart`: widget coverage نوشته‌شده برای endpoint عضو، active + تاریخ/روز، expired، no membership و payload غیرلیستی. fixture دیگر `days_remaining` جعلی ندارد.
- dependency تازه یا تغییر backend/DB/endpoint انجام نشد.

## شواهد اجراشده

- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py` → **28 فایل Dart، 0 یافته** (Tree-sitter Dart؛ گیت ایستای نحوی/الگو، نه type analysis و نه اجرای Flutter).
- الگوریتم جلالی کلاینت از `mp-app/backend/app/jalali.py` نمونه‌وار cross-check شد: 2026-03-21 → 1405-01-01 و 2026-12-10 → 1405-09-19.
- `command -v flutter` و `command -v dart` خالی بود؛ جست‌وجوی محدود مسیرهای سیستم هم executable پیدا نکرد. وابستگی‌های Python بک‌اند/pytest نیز در محیط حاضر نبودند.

## گیت اجرا‌نشده و نتیجه

- `flutter test test/membership_test.dart test/home_banner_test.dart` — **اجرا نشد**: Flutter SDK در دسترس نیست.
- `flutter analyze` / `flutter test` کامل / build — **اجرا نشدند**؛ در این loop CI نیز اجرا نشد و push انجام نمی‌شود.
- تست‌های نوشته‌شده برای unit/widget اکنون شاهد اجرای runtime نیستند. از همین رو وضعیت loop `UNKNOWN` است، نه `PASS` و نه ادعای شکست.

## تصمیم و اثر بازگشت

- D-034: بنر فقط از endpoint تاریخچه و `expires_at` استفاده کند؛ `expires_at` مرز انحصاری اعتبار است (در لحظهٔ پایان اشتراک دیگر active نیست، هم‌راستا با قاعدهٔ backend `expires > now`); timestamp بی‌zone UTC تلقی شود؛ وضعیت/تاریخ غیرقابل‌تأیید `unknown` بماند و به none/صفر تبدیل نشود. در صورت چند active معتبر، رکورد با دورترین انقضای آینده نمایش داده می‌شود.
- تصمیم برگشت‌پذیر و بدون schema/dependency است: helper/UI/provider/test hunks مربوط به M72 را می‌توان بازگرداند؛ API و دادهٔ موجود تغییر نکرده‌اند.
- بازبین خودکار مستقل، Flutter runtime، backend runtime یا E2E اجرا نشده است؛ بازبینی این گزارش و diff دستی است.

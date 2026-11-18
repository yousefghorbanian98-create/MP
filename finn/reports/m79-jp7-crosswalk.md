# M79 — crosswalk بین M5/JP7، D4/M62 و توانایی‌های ۱۴محوره

- تاریخ: 2026-11-16
- شاخه: `arena/4f336f66-mp` (فعال؛ بدون commit/push)
- وضعیت: **UNKNOWN** تا اجرای Flutter widget/analyze gate؛ crosswalk و chart gap پیاده‌سازی شده‌اند.

## Crosswalk و تصمیم scope

| معیار | route/page | منبع داده و آزمون | نتیجه |
|---|---|---|---|
| M5 / Benchmark-G6: روند JP7 عضو | GoRouter `/bodycomp` → `BodyCompPage` | `jp7TrendProvider` → `GET /assessments/jp7/member/{id}/trend`; `client/test/bodycomp_real_data_test.dart` حالت یک/دو اندازه‌گیری و منع fake percentage را دارد | route، صفحه و داده با D4 مشترک است؛ اما قبل از M79 line chart عضو در page نبود. گپ فقط chart بود. |
| D4 / M62: واقعی‌سازی پیکرسنجی | همان `/bodycomp` → همان `BodyCompPage` | همان endpoint؛ دادهٔ ناکافی، تفسیر سرور، trend summary، history و قفل درصد چربی | M62 اتصال داده و نمایش صادقانه را پوشش داده؛ این شاهد reuse می‌شود، نه اینکه صفحه/API دوباره ساخته شود. |
| توانایی‌های ۱۴محوره (M37) | AppShell tab «توانایی‌ها» → `Assessment14Page` | `/axis-assessments/member/{id}`، `/axis-assessments/{assessment_id}/matrix` و POST آزمون؛ `client/test/assessment14_page_test.dart` | قابلیت مستقلِ نتایج آزمون/ماتریس توانایی است؛ JP7 skinfold trend نیست و با M5/D4 ادغام نمی‌شود. |

## گپ مستقلِ کوچک و پیاده‌سازی

M5 با D4 در route و dataset هم‌پوشان است، ولی معیار «نمودار روند عضو» در BodyCompPage برآورده نشده بود. M79 فقط همین visualization را اضافه کرد:

- نمودار خطی بومی Flutter از `measurements[].sum_mm` مرتب‌شدهٔ پاسخ API؛ تاریخ ابتدا/انتها و مقدارهای دو سر نیز از همان response نمایش/در دسترس‌پذیری اعلام می‌شوند.
- با کمتر از دو اندازه‌گیری نمودار پنهان می‌ماند؛ هیچ نقطه، عدد یا trend محلی تولید نمی‌شود.
- provider، endpoint، route یا package/dependency موازی اضافه نشد؛ درصد چربی همچنان قفل است.
- تبدیل رقم تاریخ در `_dateFa` نیز اصلاح شد تا separator `/` باعث index خارج از محدوده نشود.
- regression widget assertions: یک measurement → chart ندارد و تاریخ واقعی رندر می‌شود؛ دو measurements → chart از دادهٔ API رندر می‌شود.

## شاهد و محدودیت

- source inspection: `client/lib/core/router.dart`, `features/bodycomp/bodycomp_page.dart`, `features/assessment14/{assessment14_page.dart,assessment14_providers.dart}`, AppShell tab، دو widget test و ردیف‌های M5/D4 TODO.
- `PYTHONPATH=/tmp/mp-dartlint python3 mp-app/client/tools/dart_gate.py --include-tests` → **53 فایل Dart، 0 یافته**.
- `flutter`/`dart` executable در sandbox موجود نیست؛ `bodycomp_real_data_test.dart`, `assessment14_page_test.dart`, `flutter analyze` و build/runtime اجرا نشدند. Static gate معادل compile/runtime نیست؛ بنابراین M79 `UNKNOWN` باقی می‌ماند.
- هیچ تغییر backend/API/route/dependency یا build/CI/production انجام نشد.

# M90 — رسید سفارش برای عضو (Flutter)

- تاریخ ثبت: ۲۰۲۶-۱۱-۱۸ (UTC)
- شاخه: `arena/4f336f66-mp`، پایه `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
- نتیجهٔ loop: **`UNKNOWN` برای runtime Flutter** — کد، تست‌ها و گیت‌های ایستای موجود سبزند؛ `flutter analyze`/`flutter test` در این sandbox اجرا نمی‌شوند (SDK نصب نیست) و نتیجه به اجرای CI موکول شده است.

## بازتولید گپ (قبل از ادعای پیاده‌سازی)

- `GET /api/v1/shop/orders/{order_id}/receipt` از M60/R5 در backend بود: `mp-app/backend/modules/shop/router.py:211` → `modules/payments/invoice.py:91 build_order_receipt`، با کنترل مالکیت `ensure_record_scope`. تست backend هم داشت.
- `GET /shop/orders` و `shopOrdersProvider` (`lib/core/app_state.dart:116`) در کلاینت وجود داشت، **ولی هیچ مصرف‌کننده‌ای نداشت**: `grep -RIn 'shopOrdersProvider' mp-app/client` فقط یک `invalidate` بعد از checkout را نشان می‌داد.
- Studio این endpoint را مصرف می‌کرد (`mp-app/studio/src/lib/api.ts:1278`)، پس گیت M71 `apiCoverage` مسیر را پوشیده بود؛ گپ دقیقاً «رسید در اپ عضو» بود، نه نبودِ API.
- نتیجه: عضو بعد از پرداخت هیچ راهی برای دیدن اقلام/وضعیت تحویل/مرجع پرداخت نداشت. هیچ مسیر تازه‌ای در backend لازم نشد.

## تغییرات

| فایل | تغییر |
|---|---|
| `lib/core/persian_format.dart` (جدید) | `faDigits` + `rial(num, {unit})` از `shop_page.dart` به `core` منتقل شد تا رسید و فروشگاه یک قالب داشته باشند |
| `lib/core/app_state.dart` | `orderReceiptProvider = FutureProvider.autoDispose.family<Map<String, dynamic>, int>`: فقط `GET /shop/orders/{id}/receipt`؛ اعتبارسنجی شکل پاسخ و **fail closed** روی `order_id` نامطابق، `member_id` نامطابق با نشست، `lines` غیرلیست، مبلغ غیر `num` و status غیررشته |
| `lib/features/shop/order_receipt_sheet.dart` (جدید) | شیت رسید: `receipt_no`، چیپ وضعیت با برچسب فارسی، تحویل‌به، تاریخ جلالی سفارش/صدور، یادداشت، تک‌تک اقلام (عنوان + واریانت + `rial(unit) × qty` + خط جمع)، «جمع اقلام» و «قابل پرداخت» جدا، بلوک پرداخت (روش/وضعیت/مرجع/زمان)، `SelectionArea` برای کپی، حالت loading/error/retry. `orderStatusLabel` وضعیت ناشناخته را ترجمه نمی‌کند (همان مقدار خام) تا سرورِ status تازه «تأییدشده» دروغ نگیرد |
| `lib/features/shop/my_orders_sheet.dart` (جدید) | «سفارش‌های من»: `RefreshIndicator` + invalidate، ردیف هر سفارش (شماره، وضعیت، تاریخ جلالی، تعداد قلم، یادداشت، مبلغ) و دکمهٔ «رسید»؛ empty و error/retry صریح |
| `lib/features/shop/shop_page.dart` | دکمهٔ «سفارش‌ها» در AppBar (ورود شیت)، رقم‌های badge سبد فارسی شد، حذف کپی محلی `faDigits`/`_rial` و استفاده از `core/persian_format.dart` |
| `test/shop_orders_receipt_test.dart` (جدید) | ۷ تست: دو unit (قالب رقم، برچسب وضعیت) + پنج widget: مسیرهای GET و «هیچ POST/PATCH از جریان رسید نمی‌رود»، رد پاسخ عضو دیگر (بی‌نمایشی مبلغ)، رد `order_id` نامطابق، نمایش هم‌زمان دو جمع ناهمخوان، خطای 503 + «تلاش دوباره» که دوباره همان مسیر را می‌خواند، و empty state |

**هیچ فایل backend/Studio/dependency/pubspec‌ای تغییر نکرد.** هیچ مبلغی در کلاینت ساخته یا ارسال نمی‌شود؛ رسید فقط‌خواندنی است و جمع‌ها از همان پاسخ سرور خوانده می‌شود (تست صریح روی نبودِ `POST`/`PATCH`).

## شواهد اجرا

| گیت | نتیجه |
|---|---|
| `dart_gate.py --include-tests` (Tree-sitter، بدون Flutter SDK) | **۶۸ فایل Dart، ۰ یافته** |
| `vitest run tests/apiCoverage.test.ts` | **4 passed** — مسیر رسید همچنان مصرف‌شده است و exception بی‌مصرف اضافه نشد |
| `npm test` (کل Studio) | **219 passed / 9 skipped** (33 فایل) — بدون رگرسیون در گیت‌های مصرف API/دیزاین‌توکن |
| Backend | بدون تغییر؛ baseline همان loop قبل: کل suite از ریشه **861 passed / 1 skipped / 1 failed** (آن شکست cwd-sensitive در `test_monitoring` است، توضیح در `finn/reports/m97-migration-drift.md`) |
| `flutter pub get` / `flutter analyze` / `flutter test` | **محلی اجرا‌نشده** — `flutter`/`dart` در sandbox نصب نیستند؛ نصب SDK از `dl.google.com` هم از این محیط ممکن نیست (فقط hostهای مشخص دسترسی دارند) |
| **CI `client-flutter` روی `776ca6f`** | **✓ سبز** — analyze + `flutter test` (۷ تست این فایل اجرا‌شده، نه skip) + manifest gate؛ مسیر رسیدن به سبز در همین گزارش است |

## محدودیت‌ها و چیزهایی که ادعا نمی‌شود

- چیدمان واقعی روی دستگاه (overflow، ارتفاع `0.78` شیت، RTL با فونت Vazirmatn) دیده نشده؛ تست ویجت در CI اجرا می‌شود ولی screenshot/golden نداریم.
- «چاپ» واقعی یا اشتراک‌گذاری فایل PDF اضافه نشد — acceptance «رسید از endpoint مالک‌محور» بود و هیچ dependency جدید (path_provider/share/pdf) لازم نشد؛ افزودنشان بدون نیاز اثبات‌شده مجاز نبود.
- رد پاسخ نامطابق، **دفاع لایهٔ کلاینت** است، نه جایگزین سرور؛ مرز واقعی مالکیت در `ensure_record_scope` باقی می‌ماند.
- شمارهٔ سفارش در تست‌ها مصنوعی است؛ هیچ دادهٔ عضو واقعی استفاده نشد.
- ECC/REA: هیچ زیرعاملی در این sandbox اجرا نشد (نه `claude`، نه REA؛ کلید API هم تنظیم نشده). بازبینی با چک‌لیست `.claude/agents/flutter-reviewer.md` و `code-reviewer.md` دستی انجام شد و به‌عنوان اجرای subagent ثبت نمی‌شود.

## اجرا در CI — دو ادعای تست که خودِ اجرا باطل کرد (۲۰۲۶-۱۱-۱۸)

run `44293699567` / job `client-flutter` (اولین اجرای واقعی پس از push بسته): **146 passed / 4 failed**، که دو موردش همین فایل بود:

| شکست | چه اتفاقی افتاد | رفع |
|---|---|---|
| `shop_orders_receipt_test.dart:191` | انتظار `۲٬۵۰۰٬۰۰۰ × ۲` بود، ولی شیت `'${rial(unitPrice)} × ${faDigits(qty)}'` را می‌سازد — یعنی `۲٬۵۰۰٬۰۰۰ ریال × ۲`. هیچ ویجتی مطابقت نکرد، چون واحد «ریال» در متن خطِ قلم هست | انتظار به متنی که واقعاً رندر می‌شود نزدیک شد؛ تست نباید قالب را از روی حافظه بنویسد |
| `shop_orders_receipt_test.dart:243` | `find.textContaining('جمع اقلام')` **دو** ویجت پیدا کرد: برچسب ردیف جمع، و جملهٔ اختلاف که خودش «با جمع اقلام یکسان نیست» را در متن دارد | `find.text('جمع اقلام')` (تطبیق کامل) + fixture با مبالغ متمایز (`۱٬۱۱۱٬۱۱۱` قلم، `۲٬۲۲۲٬۲۲۲` خط، `۴٬۰۰۰٬۰۰۰` جمع، `۵٬۰۰۰٬۰۰۰` کل، `۷٬۰۰۰٬۰۰۰` فهرست پشت شیت) تا هر `findsOneWidget` واقعاً یکی باشد |

**دو اصلاح اضافه که از همان بازبینی آمد (نه از شکست CI):** `orderReceiptProvider` حالا `items_total_rial` غیرعددی را هم رد می‌کند (وگرنه `as num?` در build ویجت TypeError می‌داد و صفحه قرمز می‌شد)، و `rial()` عدد صحیحِ نوع `double` را بدون `٫۰` نمایش می‌دهد چون JSON می‌تواند `5000000.0` بفرستد. هشدار analyze `UNNECESSARY_NON_NULL_ASSERTION` روی `_ => status!` هم حذف شد (تحلیلگر درست می‌گفت: after `null || ''` گیرنده non-nullable است).

**چیزی که تغییر نکرد:** قرارداد اصلی loop — فقط `GET`، رد payload نامطابق، و «هیچ مبلغی در کلاینت ساخته/تصحیح نمی‌شود» — همان تست‌ها سبز بودند و دست نخوردند.

**تأیید رفع در CI:** run دوم (`44295081645`، همین job) **154 passed / 2 failed** شد و **هیچ‌کدام از دو شکست مربوط به M90 نبود** — هر دو تست messenger فایل M98 بودند (باگ خودِ تخلیهٔ صف، `pumpEventQueue` زیر FakeAsync؛ ثبت در `finn/reports/m98-haptics-motion.md`). یعنی هفت تست M90 — از جمله رد payload عضو دیگر، retry روی ۵۰۳ و «فقط GET» — روی `flutter test` واقعی سبزند، و `flutter analyze` هم بدون error از همین commitها رد شد.

**وضعیت نهایی:** M90 **PASS برای دامنه‌ای که CI می‌سنجد** — `client-flutter` روی `776ca6f` (run `44300167991`) با `flutter analyze` و `flutter test` سبز، و هر ۷ تست همین فایل در همان run اجرا شدند (نه skip). اما «دیده‌شدن روی دستگاه» (overflow، ارتفاع `0.78` شیت، فونت Vazirmatn واقعی، اشتراک/چاپ) هنوز شاهده ندارد و در `LOOP-PLAN` ادعا نمی‌شود.
## بازگشت

حذف سه فایل جدید (`persian_format.dart`, `order_receipt_sheet.dart`, `my_orders_sheet.dart`)، `test/shop_orders_receipt_test.dart` و provider افزوده‌شده، و برگرداندن `shop_page.dart` به تعریف محلی `faDigits`/`_rial`، کل قابلیت را برمی‌گرداند. رفتار پرداخت/سبد تغییری نکرده است.

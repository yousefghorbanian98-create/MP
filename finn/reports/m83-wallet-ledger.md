# M83 — دفتر کامل و عضو-محور کیف‌پول

- تاریخ ثبت: ۲۰۲۶-۱۱-۱۶
- شاخه: `arena/4f336f66-mp`، وضعیت `active`، پایه `d64e3b008d1c6c20c65c5ebfa4816277d4d23ce0`
- نتیجهٔ loop: **`UNKNOWN` برای runtime اپ Flutter**. مسیر backend و Client پیاده‌سازی شده و گیت‌های backend/Studio/static سبزند؛ Flutter analyzer و widget tests اجرا نشدند چون SDK در محیط نیست.

## تغییرات پیاده‌سازی

### Backend

- مسیر جدید `GET /api/v1/payments/wallet/{member_id}/transactions` خروجی `member_id`, `balance_rial`, `transactions` و `next_before_id` می‌دهد؛ `limit` بین ۱ و ۱۰۰ و cursor با `before_id` محدود/اعتبارسنجی می‌شود.
- دفتر از `wallet_transactions` واقعی خوانده می‌شود، نه از `payments`. هر ردیف شامل شناسه، عضو، نوع `credit`/`debit`، مبلغ مثبت، توضیح و `created_at` است.
- مانده در SQL از مجموع credit منهای debit محاسبه می‌شود. balance و رکوردهای صفحه در **یک statement** برگردانده می‌شوند تا بین چند query همان پاسخ، تغییر هم‌زمان نتواند مانده را از ledger جدا کند.
- ترتیب پایدار `id DESC` (شناسهٔ جدیدتر اول) است؛ صفحهٔ بعد فقط ردیف‌های دارای `id < before_id` را می‌گیرد و cursor آخرین ردیف را برمی‌گرداند.
- `ensure_member_scope` در service اعمال می‌شود: عضو فقط دفتر خودش را می‌خواند، staff مجاز می‌تواند حساب را audit کند. دادهٔ خالی هم پاسخ صفر/فهرست خالی/null cursor می‌دهد.

### Client

- `wallet_ledger.dart` یک provider عضو-محور می‌سازد؛ پاسخ باید با `member_id` نشست تطبیق کند و تک‌تک ردیف‌ها هم باید متعلق به همان عضو باشند. شکل payload، انواع فیلدها، ترتیب نزولی و پیشرفت cursor بررسی می‌شوند؛ پاسخ ناسازگار به‌جای نمایش مانده/ردیف مشکوک، خطای قابل retry می‌دهد.
- بالای صفحهٔ Wallet، مانده از **همان پاسخ ledger** نمایش داده می‌شود؛ Client دیگر برای عدد روی صفحه به درخواست balance جداگانه‌ای که ممکن بود snapshot متفاوت داشته باشد متکی نیست.
- ردیف‌های credit/debit با علامت و توضیح واقعی، تاریخ محلی جلالی، صفحه‌بندی «تراکنش‌های قدیمی‌تر»، و حالت empty/error/retry اضافه شده‌اند. Payment history حفظ شده اما جداگانه و صریحاً جایگزین ledger نیست.
- پس از checkout فروشگاه، ledger نیز invalidate می‌شود تا تغییر debit در مراجعهٔ بعدی دوباره خوانده شود.
- تست‌های widget در `client/test/wallet_history_test.dart` منبع مانده، credit/debit، cursor pagination، empty state و رد پاسخ عضو دیگر را پوشش می‌دهند؛ این تست‌ها در این sandbox اجرا نشدند.

## شواهد اجرا

| گیت | نتیجه |
|---|---|
| M83 backend integration | `tests/integration/test_m83_wallet_ledger.py`: **2 passed**؛ شارژ/برداشت واقعی، balance، ترتیب ID، cursor pagination، member self/cross-member، staff audit و دفتر خالی |
| Payment/ownership regressions مرتبط | **13 passed** در M83 + `test_payments_deep.py` + `test_ownership.py` targeted run |
| Full backend `pytest -q` | **812 passed, 2 skipped**, 30 warnings، 95.58s |
| Ruff | `ruff check` موفق؛ `ruff format --check` برای 4 فایل backend بدون نیاز به تغییر |
| API artifact + route guard | export: **119 routes**؛ guard gate: **135 مسیر، 127 guarded، 8 public**، همه مجاز؛ `test_routes_artifact.py`: **1 passed** |
| Studio `npm test` | **33 فایل passed، 1 skipped; 219 passed, 9 skipped**؛ تست `apiCoverage.test.ts` route جدید و مصرف واقعی Client را شناسایی کرد |
| Studio `npm run build` | `tsc -b` و Vite production build موفق؛ هشدار موجود دربارهٔ dynamic/static import مانع build نبود |
| Dart static `dart_gate.py --include-tests` | **61 فایل Dart، 0 یافته** |
| Flutter `pub get`, analyze, widget/full tests, APK | **اجرا‌نشده**؛ `flutter`, `dart`, `java`, `ANDROID_HOME`, `ANDROID_SDK_ROOT` و Android SDK در sandbox موجود نیستند |

## محدوده و باقی‌مانده

- Flutter widget tests نوشته شده‌اند اما **قبول/رد runtime آن‌ها هنوز معلوم نیست**؛ `UNKNOWN` تا اجرای Flutter در محیط دارای SDK. Static Dart gate جایگزین analyzer یا widget tests نیست.
- هیچ CI/workflow، production database، پرداخت واقعی، deploy، release، push یا commit اجرا نشد.
- شاخه همان `arena/4f336f66-mp` ماند؛ baseline untracked حفظ شد و هیچ‌کدام reset یا حذف نشدند.
- پس از M83، loop مستقل بعدی طبق صف `M84` است.

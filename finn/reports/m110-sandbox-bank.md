# M110 — بانک صندباکس محلی: پرداخت «کامل» بدون هیچ حسابِ تجاری

**تاریخ:** ۲۰۲۶-۱۱-۲۰ · **وضعیت:** PASS (محلی؛ گیت‌های CI در run بعدی this branch سنجیده می‌شوند)

## چرا این loop باز شد

مالک گفت: «درگاه آنلاین همه‌چیزش تکمیل باشد؛ خودم بعداً با درگاه واقعی تست می‌کنم» — و اضافه کرد
اگر بشود با کد آزاد و کاملاً رایگان آزمودش، عالی است. دو راه قبلی هیچ‌کدام «تکمیل» نبود:

- `MockGateway` درون‌پروسه‌ای است. **حالت ندارد**: به هر authority خوش‌ساخت می‌گوید «پرداخت شد».
  نمی‌تواند «انصراف کاربر»، «پول نیامده»، «یک‌بارمصرفیِ verify» و redirect مرورگر را بازدهد.
- درگاه واقعی یعنی شناسهٔ تاجر و پول واقعی — که مالک صریحاً خواست دست‌نخورده بماند.

## چه ساخته شد

۱. **بانک صندباکس** — `mp-app/backend/devtools/sandbox_bank.py`
   یک سرویس FastAPI مستقل، رایگان، آفلاین، با همان قرارداد درگاه‌های ایرانی:
   - `POST /api/v1/purchase` → `authority`
   - `GET /pay/{authority}` → صفحهٔ RTL با سه دکمه: موفق / انصراف / موجودی ناکافی
   - بازگشت به تاجر با `302` و `?Authority=…&Amount=…&Sign=…` (امضای HMAC)
   - `POST /api/v1/verify` → ۱۰۰ بار اول، **۱۰۱ replay با همان ref_id**، ۱۰۲ مبلغ، ۱۰۳ پرداخت‌نشده، `-۱` نامعتبر/منقضی
   - `POST /api/v1/refund` → ۲۵۵ / ۲۵۴ (ایدیمپوتنت) / ۱۰۳
   - اهرم‌های آزمونِ per-txn: `ttl_seconds`، `delay_seconds`، `http_error`

۲. **آداپتر سمت اپ** — `SandboxBankAdapter` در `modules/payments/gateway.py`
   `get_gateway()` با `MP_PAYMENT_GATEWAY=sandbox` همین را می‌دهد. خطای ۵۰۰ِ بانک
   `gateway_unavailable` است نه «نامعتبر» — پرداخت pending می‌ماند، چون «نمی‌دانم» با
   «رد شد» یکی نیست. seamِ `http_client` فقط برای تست است (TestClient درون‌پروسه؛ بدون پورت).

۳. **بازگشت مرورگر** — `GET /api/v1/payments/{payment_id}/gateway-return`
   تنها مسیر عمومی payments. پیش از این چرخه فقط با deep-link اپ بسته می‌شد؛ بانک واقعی
   (و صندباکس) کاربر را با GETِ مرورگر برمی‌گرداند و هیچ مقصدی نبود. امنیت از session نمی‌آید:
   tokenِ HMACِ خودِ ما روی مبلغ + تطبیق authority با DB + verifyِ یک‌بارمصرفِ بانک.
   replay (رفرش مرورگر) صفحهٔ «قبلاً ثبت شده» می‌دهد، نه خطا، نه تسویهٔ دوباره.
   `start_payment` اگر callback_url نگیرد، خودش همین مسیر را می‌سازد (`MP_PUBLIC_BASE_URL`).

۴. **بازگشت وجه در سرویس** — `service.refund_payment` + `POST /{id}/refund`
   وضعیت تازهٔ `refunded` (ستون رشته‌ای است؛ مهاجرت لازم نداشت). سه تصمیم مستند در داکس‌رینگ:
   مرجع بازگشت در `reference_id` نوشته **نمی‌شود** (فقط audit)؛ `refunded` ≠ `failed`؛
   ۲۵۴ِ بانک = بی‌ضرر، نه خطا. `finance_summary` حالا `total_refunded_rial` و
   `refunded_count` دارد و درآمدِ بازگشتی از `total_paid_rial` بیرون می‌رود.
   درگاهِ بدون refund (Mock) صریحاً `refund_unsupported` می‌گیرد — جعلِ بازگشت ممکن نیست.

۵. **قفلِ production** — دو لایه: `validate_production_configuration` و خودِ `get_gateway()`
   هر دو `sandbox` را در production رد می‌کنند؛ تست‌ها هر دو را می‌سنجند.

۶. **سمت کلاینت** — `'refunded': 'بازگشت خورده'` در `wallet_page.dart`؛ رشتهٔ خام به UI نشت نمی‌کند.

## گیت‌ها

- `tests/integration/test_sandbox_bank.py` — **۲۲ تست** از ۳ سطح: قرارداد بانک، نگاشت‌های
  آداپتر (از جمله ۵۰۳→unavailable و unreachable)، و چرخهٔ کاملِ انسانی
  (شروع → صفحهٔ بانک → ۳۰۲ → gateway-return → تسویه/انصراف/جعل/replay → refund → مالی).
- suite کامل بک‌اند: **886 passed / 0 failed / 2 skipped** — از جمله گیت تازه‌ی
  `test_route_guard_gate` که مسیر عمومیِ تازه را اول «بدون guard» گرفت و با ثبتِ مستند در
  `PUBLIC` (نه skip) بسته شد.
- `api/routes.json` با `scripts/export_routes.py` تازه شد؛ دو ردیف exception مستند در
  `studio/tests/apiCoverage.test.ts` اضافه شد (`refund` → TODO صریح؛ `gateway-return` →
  مصرف‌کننده‌اش مرورگرِ بانک است، fileEvidence به router.py).
- رگرسیون mock: ۲۲ تست قبلیِ `test_q6_gateway.py` + `test_payments_deep.py` بدون تغییر سبز.

## چیزهایی که همین loop عوض‌شان ندانستن یعنی باگِ بعدی

- RedirectResponse استارلت پیش‌فرض **307** است — یعنی مرورگر فرم را دوباره POST می‌کند.
  هیچ بانک واقعی این‌طور نیست؛ بانک‌ها **302** می‌دهند. صندباکس هم حالا ۳۰۲ صریح است.
- Follow-redirect TestClient در تستِ خودِ بانک، آدرسِ تاجر را به همان اپ بانک می‌زند و
  ۴۰۴ می‌گیرد — «باگ بانک» به‌نظر می‌رسد، در حالی که تست باید `follow_redirects=False` باشد.
- گیت «مسیر دکوراتیو» با تستِ تازگیِ `api/routes.json` هر مسیر تازه را **همین‌جا** گیر می‌اندازد؛
  جای درستِ ثبتِ استثنا همان `ROUTE_EXCEPTIONS` با evidence قابل‌راستی‌آزمایی است، نه quiet-skip.

## محدودیت‌های صریح (هیچ‌کدام «سبز» گزارش نمی‌شوند)

- M111: ستون `refund_reference` و UI بازگشت وجه (acceptance-panel) هنوز ساخته نشده — refund
  شناسهٔ بانکش فعلاً فقط در audit است.
- رسید/فاکتورِ بازگشت وجه ساخته نشده؛ صورت‌حساب عضو رفتارِ امروز را نشان می‌دهد.
- تستِ درگاه واقعیِ زرین‌پال با شناسهٔ تاجرِ خودِ مالک — طبق تصمیم، وظیفهٔ او؛ دستورکارش:
  `MP_PAYMENT_GATEWAY=zarinpal` + `MP_PAYMENT_SANDBOX=true` + `MP_ZARINPAL_MERCHANT_ID=…`.
- صندباکس state درون‌حافظه‌ای است و عمداً همین‌طور مانده؛ ری‌استارت = تراکنش‌ها می‌روند.
  این برای «بانکِ آزمون» درست است، نه برای هیچ سرویس واقعی.

## Rollback

بدون مهاجرت DB. بازگشت = revert همین commit؛ تنها اثرِ پایداری `routes.json` و دو ردیف
exception استودیو است که با همان revert می‌روند.

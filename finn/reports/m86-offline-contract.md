# M86 — قرارداد محدود و fail-closed برای Offline Outbox

- تاریخ: 2026-11-17
- وضعیت: **PASS (قرارداد)** — بدون ادعای پیاده‌سازی کلاینت؛ M87/M88 جدا هستند.
- سند به‌روز: `docs/MuscleParadise/ANDROID-OFFLINE-PLAN.md`

## انتخاب قرارداد

- فقط بازخورد ساختاریافتهٔ تمرین برای `POST /programs/sync/set-feedback` قابل صف است.
- شناسهٔ مالک از نشست جاری گرفته می‌شود. شناسه‌های ثابت `device_id` و `client_id` و زمان اصلی برای retry نگه داشته می‌شوند؛ سمت سرور هویت کلید `(member_id, device_id, client_id)` و حل تعارض LWW است.
- allowlist آفلاین شامل program/movement، وزن، target/done reps، RIR و زمان است؛ note آزاد، soreness/درد، چهره/زیست‌سنجی، پرداخت، رزرو، check-in، غذا، چت، OTP و CRUD عمومی صف نمی‌شوند.
- پاسخ server، conflict/stale/clock-skew، retry/backoff، ack قبل از پاک‌سازی، وضعیت قابل مشاهده، owner binding و خروج/account switch به‌صورت fail-closed تعریف شدند.
- قرارداد storage را به Android app-private با `allowBackup=false` محدود می‌کند؛ application-layer encryption وجود ندارد و policy رمزنگاری دستگاه از این کد قابل‌اثبات نیست. به همین دلیل M87 پرچم `MP_ANDROID_OFFLINE_FEEDBACK_ENABLED` را پیش‌فرض خاموش می‌گذارد تا تأیید جداگانهٔ دستگاه/محیط.
- خروج/تغییر شماره با صف حل‌نشده انتخاب صریحِ نگه‌داشتن owner-bound data یا حذف قطعی همان owner را می‌خواهد؛ owner دیگر آن را نه می‌خواند نه می‌فرستد. Web/PWA offline-only نیست.

## شاهد

- Backend contract موجود: `tests/integration/test_m57_sync.py` شامل LWW، retry/idempotency، stale-write، clock-skew، دو device، member ownership و سقف 500 item: **12 passed**، دو هشدار deprecation شناخته‌شده.
- هیچ client DB، dependency یا runtime در M86 اضافه نشد؛ رفتارهای restart/UI/logout هنوز پذیرش M87 هستند.

## بازگشت

فقط بخش M86 از `ANDROID-OFFLINE-PLAN.md` و گزارش را برگردان؛ داده، migration و side effect خارجی وجود ندارد.

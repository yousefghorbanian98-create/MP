# MEM-CLOSE — جمع‌بندی ۱۶ آیتم MEM (فاز A)

> snapshot در HEAD همین commit. `PARTIAL/NOT_ACCEPTED` یعنی «ساخته و با تست و mutation
> اثبات‌شده، ولی بدون بازبین مستقل و بدون اجرای مرورگر/دستگاه پذیرش نشده».
> مرز بیرونی (بخش ② دستورنامه) برای همهٔ ردیف‌ها برقرار است: device/browser/reviewer.
> «—» در ستون mutations یعنی فایل mutation-proof مستقل برای آن برش در این مخزن نیست؛
> یعنی «صفر mutation» ادعا نمی‌شود.

| # | عنوان | mutations | تست‌ها | وضعیت | یادداشت |
|---|---|---|---|---|---|
| MEM-01 | shell عضو (PWA-30) | — | 9 live-contract + 33 focused | PARTIAL/NOT_ACCEPTED | شواهد کافی؛ پذیرش نیازمند اجرای مرورگر (evidence/2026-11-27/MEM-01) |
| MEM-02 | حساب و عضویت (PWA-31) | 2 | 6 (memberAccount.test.ts) + 14 با صفحه (memberAccountPage.test.tsx) | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-03 | تغییر شماره/نشست دستگاه (PWA-32) | — | — | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-04 | دسترسی برنامه (PWA-33) | — | — | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-05 | ثبت فیدبک ست (PWA-34) | — | — | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-06 | گیت ایمنی برنامه (PWA-35) | 3 | — | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-07 | روند ارزیابی (PWA-36) | — | — | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-08 | تغذیه (PWA-37) | 3 | 5 (memberNutrition.test.tsx) + 3 mutation | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-09 | کلاس/رزرو (PWA-38) | 3 | 7 (memberClasses.test.tsx) + 3 mutation | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-10 | حضور QR (PWA-39) | 2 | 4 (memberCheckin.test.tsx) + 2 mutation + 7 پشتیبان integration | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-11 | کیف پول (PWA-3A) | 2 | 5 (memberWallet.test.tsx) + 2 mutation + پشتیبان test_m83_wallet_ledger.py | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-12 | فیش کارت‌به‌کارت (PWA-3B) | 3 | 7 (memberPayments.test.tsx) + 3 mutation + 66 پشتیبان integration/regression | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-13 | فروشگاه نمایشی (PWA-3C) | 2 | 5 (memberShop.test.tsx) + 2 mutation + 8 پشتیبان integration | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-14 | چت (PWA-3D) | 3 | 6 (memberChat.test.tsx) + 3 mutation | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-15 | اعلان (PWA-3E) | 2 | 6 (memberInbox.test.tsx) + 2 mutation | PARTIAL/NOT_ACCEPTED | موجود |
| MEM-16 | outbox آفلاین (PWA-3F) | — | — | BLOCKED | policy آفلاین/رمزنگاری/TTL/sync تصویب نشده (TODO line 244) |

## Loose ends ثبت‌شده (نه پنهان)
- MEM-14: سرور برای ارسال پیام idempotency ندارد (`GAP` در `../MEM-14/contract-answer.txt`).
- MEM-16: `BLOCKED` طبق policy سند (encryption/TTL/sync/conflict/revoke/wipe تصویب نشده).
- MEM-01: شواهد موجود کافی است ولی پذیرش نیاز به اجرای مرورگر دارد؛ همین‌جا `PARTIAL` می‌ماند.
- MEM-12/STAFF-05: تأیید فیش با مرجع بانکی مستقل = تصمیم مالک (بخش ② بند ۵).

# MEM-02 / PWA-31 — حساب و عضویت (بازبینی دور ۱)

```text
MEM-02/PWA-31=PARTIAL/NOT_ACCEPTED
WORK=بازبینی + mutation؛ کد محصول تازه لازم نبود
STATES=active | expiring | expired | cancelled | unknown
TESTS=6 (memberAccount.test.ts) + 14 با صفحه (memberAccountPage.test.tsx)
MUTATIONS_PROVEN=2
```

- منطق پنج‌حالته از قبل هست: `src/lib/memberAccount.ts:44-59` —
  `cancelled`/`expired` صریح، هر وضعیت ناشناخته ⇒ `unknown` (نه active)، و انقضا از
  **لحظهٔ دقیق** `expires_at` محاسبه می‌شود نه از job زمان‌بندی‌شده.
- صفحه: `src/pages/MemberAccount.tsx:205-230` هر عضویت را با همان view رندر می‌کند.
- mutation (هر دو قرمز و بازگشت byte-identical):
  `unknown → active` · `remainingMs<=0 → active`
  ([`mutation-proof.txt`](mutation-proof.txt)).
- دامنه: پروفایل/عضویت از `GET /members/me` و `GET /members/{id}/memberships` با
  `ensure_member_scope` سمت سرور؛ هیچ endpoint تازه‌ای ساخته نشد.

## باز (چرا PARTIAL)
بدون بازبین مستقل و بدون اجرای مرورگر/دستگاه؛ ویرایش پروفایل از سمت عضو در این برش نیست.

# MEM-10 / PWA-39 — حضور با QR (2026-11-27)

```text
MEM-10/PWA-39=PARTIAL/NOT_ACCEPTED
CONTRACT=POST /face/checkin-qr ⇒ INSERT تازه؛ یکتایی روی checkins.qr_jti_hash
NEW_ENDPOINT=no
UI=MemberCheckin.tsx روی /member/checkin
TESTS=4 (memberCheckin.test.tsx) + 2 mutation + 7 پشتیبان integration
```

- قرارداد: [`contract-answer.txt`](contract-answer.txt). `db.add(ci)`/`db.commit()` در
  `modules/face_id/service.py:191-236` و ایندکس یکتا
  `uq_checkins_qr_jti_hash` روی `checkins.qr_jti_hash` (`db/models/face_id.py:52`،
  migration `c5d6e7f8a9b0_m65_qr_replay_guard.py:21`).
- سه حالت پشتیبان از قبل تست شده‌اند و **دوباره اجرا شدند**:
  `pytest tests/integration/test_m65_qr_security.py` ⇒ 7 passed
  (replay ⇒ 409 `qr_replayed` :144/:156، منقضی ⇒ رد :160، عضو دیگر ⇒ 403 :131،
  چهره fail-closed 409 :64). ⇒ تست بک‌اند تازه لازم نبود.
- UI: توکن از `GET /face/qr-token` گرفته و **فقط در state** نگه داشته می‌شود (نه
  localStorage، نه URL)؛ تاریخچه از `GET /membership/me/checkins`.
- متن الزامی: «حضور شما برای این نشست ثبت شد؛ تأیید نهایی توسط مربی/سیستم.» —
  هرگز «حضور ثبت شد ✅»؛ به‌علاوه «QR به‌تنهایی حضور یا هویت را اثبات نمی‌کند».
- گیت‌ها در تست: نبود توکن در localStorage؛ صفر فراخوانی به `/face/checkin`
  (بدون بازشناسی چهره)؛ ۴۰۳ ⇒ `role="alert"` و صفر ردیف تاریخچه.
- mutation: ذخیرهٔ توکن در localStorage و متن «حضور ثبت شد ✅» ⇒ هر بار یک تست قرمز،
  بازگشت سبز ([`mutation-proof.txt`](mutation-proof.txt)).

## BLOCKED (اجباری — پوشش حضور/ایمنی)
- «تأیید نهایی توسط مربی» در این برش **فقط متن است**؛ هیچ جریان تأیید مربی در UI بررسی
  نشده و ما آن را ادعا نمی‌کنیم (`mp-app/studio/src/components/MemberCheckin.tsx` —
  بخش متن تأیید). تصمیم دربارهٔ اینکه چه کسی/چگونه حضور را قطعی می‌کند = مالک/مربی.
- اسکن واقعی QR با دوربین دستگاه اجرا نشده (دستگاه/مرورگر `NOT_RUN`).

## باز (چرا PARTIAL)
جریان تأیید مربی، آفلاین/بدون‌شبکه، و اجرای دستگاه نداریم؛ تعداد ردیف‌های تاریخچه
بدون صفحه‌بندی محدود به سرور است.

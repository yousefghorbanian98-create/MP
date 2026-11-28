# MEM-06 / PWA-35 — گیت ایمنی در مسیر عضو (2026-11-27)

```text
BRANCH=arena/3c08bfbd-mp
BASE=main@7c4771f (squash of #31؛ درختِ شاخه با main یکی است)
MEM-06/PWA-35=PARTIAL/NOT_ACCEPTED (checkbox TODO باز است)
YIELDING_FINDING=MemberTodayProgram سه وضعیت ایمنی را به یک پیام واحد تبدیل می‌کرد
BACKEND_ENDPOINT_ADDED=no — قرارداد و موتور از قبل موجود بود
EXECUTABLE_RULE=status=="clear" AND safe_to_generate==true (تنها حالت)
BLOCKED_FOR_MISSING_DATA=no — ProgramOut.safety_flags کل پرچم را برای عضو برمی‌گرداند
```

## یافته
`mp-app/studio/src/components/MemberTodayProgram.tsx:203-211` (پیش از تغییر) هر سه وضعیت
`blocked` / `needs_review` / `clear` را با یک جمله نشان می‌داد: «غربالگری ایمنی این برنامه
خالی نیست؛ پیش از اجرا با مربی مرور کنید.» یعنی برنامهٔ `blocked` هم به‌عنوان برنامهٔ
قابل‌اجرا ارائه می‌شد. `SafetyBadge` که تفکیک چهار وضعیت را داشت فقط در
`pages/Programs.tsx` (shell کارکنان) استفاده می‌شد.

این نقض معیار پذیرش `MEM-06`: «هیچ safety flag صرفاً برای ثبت یا warning دور زده نشود».

## کاری که انجام شد (بدون ساخت endpoint تازه)
1. `studio/src/components/ProgramSafetyPanel.tsx` (تازه): چهار وضعیت با چهار متن و
   چهار رنگ؛ `safetyStatus()` هر مقدار ناشناختهٔ سرور را به `unknown` تنزل می‌دهد (نه `clear`)،
   `isExecutable()` فقط `clear + safe_to_generate=true` را مجاز می‌داند، و
   `executionBlockReason()` برای هر چهار حالت **متن متفاوت** دارد.
2. `MemberTodayProgram.tsx`: پنل ایمنی + دروازهٔ اجرا. در وضعیت غیرمجاز، فهرست حرکات و
   فرم ثبت ست رندر نمی‌شود، یک `<button disabled>شروع تمرین</button>` با
   `aria-describedby` به متن دلیل، و متن دلیل به‌صورت **دیده‌شدنی** (نه tooltip) نمایش داده می‌شود.
3. `tests/safetyBadge.test.tsx`: ۸ تست تازه — از جمله مقایسهٔ متن کامل چهار رندر و
   جدول درستی `isExecutable` و یکتا بودن دلیل‌ها.
4. `tests/memberTodayProgram.test.tsx`: ۵ تست تازه روی مسیر عضو (blocked / needs_review /
   unknown / corrupt / clear).
5. `tests/setFeedback.test.tsx`: فیکسچر برنامه حالا پرچم `clear` دارد — چون فرم ثبت ست
   فقط پشت دروازهٔ اجرا رندر می‌شود (این تغییر رفتار آگاهانه است و در فیکسچر توضیح داده شد).
6. `tests/integration/test_m56_safety_gate.py`: ۲ تست تازه که پرچم را از **مسیر عضو**
   (`GET /api/v1/programs/member/{id}`) می‌سنجند، نه از ستون دیتابیس.

## نتیجه‌های اجراشده
```text
vitest tests/safetyBadge.test.tsx        → 17 passed
vitest tests/memberTodayProgram.test.tsx → 9 passed
vitest tests/setFeedback.test.tsx        → 4 passed
vitest (کل)                              → 57 فایل pass / 4 skip · 416 تست pass / 15 skip
pytest tests/integration/test_m56_safety_gate.py → 8 passed
tsc -b / eslint . / npm run build        → پاک / پاک / ✓
```

## تغییر رفتار آگاهانه (قابل بازگشت)
هر برنامهٔ `approved` که پرچم ایمنی‌اش `{}` یا `unknown` است، دیگر فهرست حرکات و فرم ثبت
را به عضو نشان نمی‌دهد؛ به‌جایش «غربالگری نشده — نه بی‌خطر» و دلیل توقف اجرا می‌بیند.
این تصمیم از معیار پذیرش MEM-06 می‌آید (نبود پرچم = نامعلوم، نه مجاز)، ولی یعنی برنامه‌های
قدیمیِ بدون غربالگری تا اجرای مجدد غربالگری اجرایی نیستند. اگر محصول تصمیم بگیرد فهرست
حرکات در وضعیت `unknown` فقط «نمایشی» باشد، تغییر در یک شرط `executable` کافی است.

## چیزهایی که همچنان باز است (به همین دلیل PARTIAL)
- reviewer/متخصص ایمنی مستقل: ندارد (`UNKNOWN`)، پس checkbox بسته نمی‌شود.
- اجرای واقعی روی دستگاه/مرورگر: انجام نشده.
- `blocked` هنگام تأیید برنامه توسط مربی هنوز می‌تواند `approved` شود (گیت سمت تأیید
  در این برش تغییر نکرد) — این تصمیم محصول است، نه باگ UI.

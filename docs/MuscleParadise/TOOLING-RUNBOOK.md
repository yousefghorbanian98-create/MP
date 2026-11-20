# راهنمای بازیابی ابزارها و دارایی‌های خارج از Git — TOOLING-RUNBOOK

> هدف: **هیچ‌چیز حیاتی فقط در sandbox نماند.** هر آنچه بازساختنی است، دستور بازسازی‌اش اینجاست؛ هر آنچه یکتاست، در workspace/Git ثبت می‌شود. دستورهای قدیمیِ commit+push به‌صورت پیش‌فرض مجاز نیستند؛ بااین‌حال کاربر برای checkpoint امنیت/عملیاتِ بازبینی‌شده، یک commit/push محدود به شاخهٔ جاری `arena/4f336f66-mp` را صریحاً مجاز کرده است (D-046). این استثنا مجوز release/deploy/rollback یا تغییر production نیست؛ artifacts محلی حفظ می‌شوند.

## ۱. بستهٔ fitness-handoff ✅ در Git
- فایل: `docs/MuscleParadise/handoff/fitness-handoff-2026-11-11.zip` (SHA-256: `f8113944fb2c60a6bfcfa3d1df0458538802954ab8eda6215e68c8ad78441e0e`)
- بازدریافت (در صورت نیاز):
  `gh api -H "Accept: application/vnd.github.raw" "repos/yousefghorbanian98-create/Cutting-Edge-Studio./contents/delivery/fitness-handoff-2026-11-11.zip?ref=68f8454bf093e89c01bee0675765d0289b6ae5d1" > fitness-handoff.zip`
- تحلیل کامل: `docs/MuscleParadise/HANDOFF-ANALYSIS-2026-11-14.md` (VERIFY.py = PASSED)

## ۲. semgrep (اسکن امنیتی) — venv جدا (درس: نصب روی venv محصول ممنوع)
```bash
python3 -m venv /tmp/tools-venv
/tmp/tools-venv/bin/pip install semgrep
git clone --depth 1 https://github.com/semgrep/semgrep-rules /tmp/semgrep-rules
/tmp/tools-venv/bin/semgrep --config /tmp/semgrep-rules/python --metrics=off mp-app/backend
```
- وضعیت آخر (۲۰۲۶-۱۱-۱۴): **۰ یافته** در بک‌اند (M22-c1/c2).

## ۳. Face-ID — اثبات‌شده PASS (M-consult)
- پشته (PyPI، رایگان/آفلاین): `dlib-bin` + `face_recognition_models` + `face_recognition` + `setuptools==80.9.0` + `Pillow` + `click`
- مدرک: `finn/reports/faceid-evidence/faceid-proof.json` + سه تصویر ساختگی (قاعدهٔ E09: بدون دادهٔ واقعی)
- نتیجه: تأیید ۱:۱ (A↔A2: 0.564<0.6 MATCH) + شناسایی ۱:N درست | یافته‌های مهندسی: HOG روی صورت سه‌رخ می‌شکند → CNN fallback؛ CNN روی تصویر بزرگ OOM → کوچک‌سازی ۶۴۰px اجباری
- مدل‌های YuNet/SFace اصلی در sandbox قابل دریافت نبود (Git-LFS مسدود) — جایگزین MIT انتخاب شد؛ در محیط واقعی: `git clone https://github.com/opencv/opencv_zoo` (با git-lfs) یا همان پشتهٔ dlib.

## ۴. تست بار — Locust (کاربران فیک) ✅ اجراشده
```bash
/tmp/tools-venv/bin/pip install locust
cd mp-app/backend && ../../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000   # ترمینال ۱
/tmp/tools-venv/bin/locust -f mp-app/backend/tests/load/locustfile.py --headless -u 40 -r 8 -t 20s --host http://127.0.0.1:8000 --csv=finn/reports/load/M22-smoke
```
- نتیجهٔ M22-smoke: ۸۳۵ درخواست/۲۰s، p95=13ms، **صفر کرش**؛ ۲۴۵×۴۲۹ = rate-limit درست کار کرد. گزارش: `finn/reports/load/M22-smoke-report.md`

## ۵. گیت‌های استاندارد هر میکرو-لوپ
```bash
cd mp-app/backend && ../../.venv/bin/pytest -q && ../../.venv/bin/ruff check .      # بک‌اند
cd mp-app/studio && npx vitest run && npm run lint 2>/dev/null || true              # استودیو (CI نیز می‌گیرد)
# فلاتر در CI: flutter analyze + flutter test (D-002/003 — در sandbox نصب‌نشدنی)
/tmp/tools-venv/bin/semgrep --config /tmp/semgrep-rules/python --metrics=off mp-app/backend
```

## ۶. قواعد ماندگاری
- سند/نتیجه/گزارش در workspace و مسیر پروژه ذخیره و ارجاع‌پذیر باشد؛ push خودکار/فوری ممنوع است. برای همین checkpoint فقط، کاربر commit و push بازبینی‌شده به شاخهٔ جاری را صریحاً مجاز کرده است؛ مجوزی برای branch دیگر، release یا deploy نیست.
- باینری‌های بازساختنی (مدل‌ها، venvها) → فقط دستور + منبع + hash در این سند.
- دادهٔ واقعی هرگز (E09) — نمونه‌ها ساختگی‌اند؛ هیچ credential یا دادهٔ عضو وارد Git/log نمی‌شود.

## ۷. قاعدهٔ شاخه — تصمیم مالک ۲۰۲۶-۱۱-۲۰: یک تنه، شاخه‌های کوتاه‌عمر

قاعده ساده است و برای همیشه:

1. `main` تنها شاخهٔ دائمی است و در زمان ارائه، `main` حالت نهایی پروژه است.
2. توسعه در **یک** شاخهٔ کوتاه‌عمر از `main` انجام می‌شود؛ هم‌زمان بیش از یک شاخهٔ فعال نگه نمی‌داریم.
3. پایان کار: PR → CI سبز روی همان SHA → merge → **همان لحظه حذف شاخه**.
4. شاخهٔ مرج‌شده یا بی‌کامیت یکتا («خالی») حذف می‌شود؛ شاخهٔ دارای کار یکتا هرگز پاک نمی‌شود.
5. هر چیزی که فقط ارزش مرجع دارد (نه ادامهٔ کار) → **تگ آرشیو** و حذف شاخه؛ الگویش: [BRANCH-CONSOLIDATION-2026-11-20](BRANCH-CONSOLIDATION-2026-11-20.md).

چک‌های عملی:

```bash
git ls-remote --heads origin                       # در زمان ارائه باید فقط main را نشان دهد
git fetch --prune origin && git branch -r | grep -v main   # هیچ شاخهٔ دوردست دیگری نماند
gh api -X DELETE repos/<owner>/<repo>/git/refs/heads/<branch>   # فقط پس از merge یا تگ آرشیو
```

**یک تنظیم که فقط مالک می‌تواند روشن کند:** GitHub → Settings → General →
«Automatically delete head branches». با آن، هر merge خودکار شاخهٔ منبع را حذف می‌کند و
قاعدهٔ بند ۳ به‌صورت مکانیکی اجرا می‌شود. توکن فعلی اجازهٔ تغییر این تنظیم را ندارد
(403)؛ تا روشن‌شدنش، حذف دستی در همان PR انجام می‌شود.

> تنها استثنا: شاخهٔ نشست جاری ابزار (Arena) تا وقتی نشست فعال است حذف نمی‌شود؛
> محتوایش وقتی merge شد دقیقاً برابر `main` است.

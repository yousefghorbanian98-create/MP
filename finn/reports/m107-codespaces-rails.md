# M107 — ریل اجرای گیت‌های بیرون از sandbox (Codespace + دستگاه) و رفع شکنندگی cwd

- تاریخ: ۲۰۲۶-۱۱-۱۸ · شاخه: `arena/4f336f66-mp` · پایهٔ حلقه: درخواست کاربر — «کارهایی که اینجا نشد را دور بزن؛ من Codespaces را فعال می‌کنم، قدم‌به‌قدم بگو تا همان‌جا اجرا کنم»
- دامنه: **راه‌اندازی و مستندسازی** — نه اجرای Codespace، نه ساخت ماشین، نه build اندروید، نه لمس keystore

## ۱) گپ و آنچه همین‌جا انجام شد

سه چیز در agent sandbox هرگز قابل اجرا نبود و status برخی loopها به همین دلیل `UNKNOWN` ماند:
Flutter/Dart SDK، Android SDK/Gradle، و `pip-audit` روی محیطِ ساخته‌شده از `pyproject.toml`.
Codespaces سه تای اول را ممکن می‌کند؛ بخشی از چهارمی (دستگاه واقعی) **هیچ‌وقت** در Codespace شدنی نیست —
Codespaces به USB دسترسی ندارد و KVM برای emulator ندارد. پس دستور کار به دو مسیر split شد.

| تغییر | چه |
|---|---|
| `docs/MuscleParadise/runbooks/codespaces-execution.md` | دستور کار مرحله‌به‌مرحله (۰ تا ۸) با خروجی مورد انتظار، قالب ارسال لاگ، و جدول «هر شاهد ↔ کدام loop» |
| `.devcontainer/provision-android-sdk.sh` | نصب **اختیاری** Android SDK برای شاهد کامپایل (debug فقط، بدون keystore) — با reject کردن نصب بدون checksum مگر تأیید صریح |
| `.devcontainer/README.md` | توضیح اینکه چرا SDK در build تصویر نیست (پذیرفتن license باید عمل انسان باشد) و اینکه اسکریپت **توسط نویسنده‌اش اجرا نشده** |
| `scripts/docs_gate.py` | فایل تازه به فهرست لینک‌چک اضافه شد (۹ فایل / ۱۰۴ لینک / ۴ Mermaid سبز) |
| `docs/README.md` | سطر «تست، انتشار یا عملیات» به runbook لینک شد |
| `mp-app/backend/tests/integration/test_monitoring.py` | `Path("../infra/monitoring/alerts.yml")` → `Path(__file__).resolve().parents[3] / "infra/monitoring/alerts.yml"` |
| `finn/reports/m97-*.md`, `m99-*.md` | ارجاع «ثبت شد، اصلاح نشد» به رفع به‌روز شد (نه بازنویسی تاریخ) |

## ۲) گیت‌های همین loop

| گیت | نتیجه |
|---|---|
| `pytest -q mp-app/backend/tests` **از ریشهٔ مخزن** | **873 passed / 1 skipped** در ۲۱۰s — پیش از این رفع: 861 passed / **1 failed** از همان cwd |
| `pytest -q tests` از `mp-app/backend` | **873 passed / 1 skipped** — هر دو cwd یک عدد (منطق تست دست‌نخورده؛ فقط مسیرخوانی) |
| `bash -n .devcontainer/provision-android-sdk.sh` | syntax OK (تنها بررسی ممکن در این محیط) |
| `python3 scripts/docs_gate.py` | ۹ فایل · ۱۰۴ لینک محلی · ۴ Mermaid · SVG XML ✓ |
| `flutter analyze` / `flutter test` / `flutter build apk` | **اجرا‌نشده** — SDK نیست؛ و دسترسی به `storage.googleapis.com` هم مسدود است. شاهدشان در همین runbook برای Codespace است |
| اجرای اسکریپت provisioning | **اجرا‌نشده و test‌نشده** — به همین دلیل در سند «اولین اجرا خودش یک گیت است» نوشته شده و حالت پیش‌فرضش «نصب نکردن» است |

## ۳) آنچه این loop ادعا نمی‌کند

- هیچ Codespace ساخته/هزینه نشد؛ هیچ لاگی از Flutter/Gradle وجود ندارد؛ پس هیچ status محصولی به‌خاطر «runbook نوشته شد» عوض نشد.
- اسکریپت provisioning شمارهٔ بیلد cmdline-tools را به‌عنوان **پیش‌فرض** دارد (قابل override با env) ولی hash را نمی‌سازد؛ اگر `SDK_SHA256` داده نشود، عمداً exit 2 می‌کند.
- `apk.yml` را trigger نکردم: آن workflow با keystore موجود در مخزن امضا می‌کند و تا تصمیم SEC-01، بیلد امضاشدهٔ تازه نساختنی است (در runbook هم با همین هشدار آمده).
- قدم‌های ۶ (دستگاه) روی لپ‌تاپ اجرا می‌شوند؛ هیچ عدد startup/mask/haptics از پیش «تقریب» نشده است.

## ۴) بازگشت

حذف `runbooks/codespaces-execution.md` + `provision-android-sdk.sh`، برگرداندن `.devcontainer/README.md`،
`docs/README.md`، ردیف `docs_gate.py`، و یک revert برای `test_monitoring.py`. هیچ‌کدام رفتار runtime ندارند؛
تنها گیت backend که جابه‌جا می‌شود همان یک تست است و از هر دو cwd سبز می‌ماند (revert فقط دوباره cwd-حساسش می‌کند).

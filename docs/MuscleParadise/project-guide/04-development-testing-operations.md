# ۴. توسعه، آزمون، CI و عملیات

[بازگشت به راهنما](README.md) · [Backend/API](02-backend-and-data.md) · [Release checklist](../RELEASE-CHECKLIST.md) · [Deployment notes](../DEPLOYMENT.md)

## ۴.۱ پیش‌نیازها

| جزء | حداقل/CI | ابزار |
|---|---|---|
| Backend | Python 3.11+ | `pip`, Uvicorn; dev extras برای pytest/Ruff/security. |
| Studio | Node.js 22 در CI | npm؛ `package-lock.json` برای `npm ci`. |
| Client | Flutter/Dart مطابق pin `.devcontainer/Dockerfile`; CI Client pin فعلی 3.50.0 | Android build tools برای debug APK؛ build release/signing گیت جدا دارد. |
| Infra | Docker Compose, reverse proxy/DNS/TLS برای stack مناسب | این ابزارها صرف وجود فایل deployment نصب/پیکربندی‌شده فرض نمی‌شوند. |

پیش از اجرا نسخه‌های واقعی محیط را ثبت کنید. SDK شناور `stable` در بعضی jobها وجود دارد، ولی job `client-pinned` نسخه و revision devcontainer را تطبیق می‌دهد.

## ۴.۲ اجرای محلی گام‌به‌گام

### ۱) Backend توسعه با دیتابیس جدا

از ریشهٔ repo:

```bash
cd mp-app/backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -c requirements.txt -e ".[dev]"

# اپ اکنون محیط را صریح می‌خواهد. DB در فایل محلی مجزا باشد.
export MP_ENVIRONMENT=development
export MP_DATABASE_URL=sqlite:///./mp-dev.db
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

در development، lifespan فعلی `init_db()`/`create_all` را اجرا می‌کند. این برای دیتابیس محلی خالی مناسب است؛ migration production نیست. `/health` را می‌توان برای liveness دید؛ API docs معمول FastAPI زیر `/docs` است. OTP dev پیامک واقعی نمی‌فرستد. اگر برای smoke محلی نیاز به code echo دارید، فقط روی دیتابیس/حساب ساختگی از `MP_ALLOW_DEV_OTP_ECHO=true` استفاده و پس از آزمون پاک کنید؛ این گزینه در production رد می‌شود و کد OTP را در محیط واقعی/اسکرین‌شات/لاگ نگذارید.

### ۲) Studio با proxy به API

ترمینال جدا:

```bash
cd mp-app/studio
npm ci
MP_API_TARGET=http://127.0.0.1:8000 npm run dev -- --host 0.0.0.0
```

Vite host/allowed host را در `vite.config.ts` تنظیم می‌کند و `/api`, `/health` را به target می‌فرستد. مرورگر از همان origin درخواست می‌کند؛ از client code به `localhost` متصل نشوید. مسیر dev UI را از log Vite بردارید.

### ۳) Flutter Client / Android emulator

ترمینال جدا:

```bash
cd mp-app/client
flutter pub get
flutter analyze --no-fatal-infos
flutter test
flutter run --dart-define=MP_API=http://10.0.2.2:8000/api/v1
```

`10.0.2.2` معمولاً host-loopback از Android Emulator است؛ در تلفن واقعی باید IP LAN یا HTTPS domain قابل‌دسترسی همان گوشی داده شود. Client عمداً HTTP روی میزبان عمومی را رد می‌کند. `MP_API` را به endpoint production یا دادهٔ واقعی بدون گیت‌های owner/security وصل نکنید.

### مسیر اجرای تست‌ها

فرمان‌های متداول (از پوشهٔ مربوطه):

```bash
# Backend
cd mp-app/backend
pytest -q
bash scripts/coverage_run.sh
ruff check .
ruff format --check .

# Studio
cd ../studio
npm test
npm run lint
npm run build

# Flutter Client
cd ../client
flutter analyze --no-fatal-infos
flutter test
flutter build apk --debug

dart format --output=none --set-exit-if-changed lib test tools

# مستندات/نقشه‌ها از ریشهٔ repo
cd ../..
python3 scripts/docs_gate.py
python3 scripts/interaction_map.py --check
```

`coverage_run.sh` تست را با coverage اجرا، فایل XML/JSON می‌سازد و `coverage_gate.py` را با حداقل‌های per-directory فراخوانی می‌کند. این اسکریپت فایل‌های coverage را پاک/بازمی‌سازد؛ فقط در checkoutی اجرا کنید که این اثر تولیدی پذیرفته شده باشد. آزمون کامل در این turn اجرا نشده است؛ هیچ عدد pass/coverage این سند گزارشِ امروز نیست.

### دربارهٔ شمارش آزمون‌ها

در snapshot فعلی فهرست فایل‌ها، حدود ۳۶ فایل `test_*.py` در `tests/unit`, ۹۸ فایل در `tests/integration`, ۲۸ فایل Dart در `client/test` و ۵۲ فایل `.test.*` در `studio/tests` شمرده شد. این‌ها **تعداد فایل**اند، نه تعداد case، نه PASS، و نه پوشش مسیرهای production. Backend همچنین پوشه‌های `regression`, `e2e`, `load`, `evaluation` دارد. نتیجهٔ تاریخی مثل «۱۳۳۳ پاس/۲ skip/۹۱٪» به همین SHA/worktree تعمیم‌پذیر نیست؛ برای status واقعی suite/CI همان SHA را اجرا/مشاهده کنید.

## ۴.۳ CI: چه چیزی واقعاً gate می‌شود

Workflow اصلی [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml) pipeline چندجزئی دارد:

| job/مرحله | گیت و مرز |
|---|---|
| `secret-scan` | Gitleaks full Git history، نسخه/checksum بررسی‌شده و خروجی redacted؛ synthetic test برای استثناهای دقیق. PASS روی commit قدیمی به HEAD جدید یا dirty source تعمیم ندارد. |
| `docs` | `scripts/docs_gate.py`, `interaction_map.py --check`, parser رسمی Mermaid و `repo_hygiene_gate.py`. این گیت‌ها متن/لینک/diagram/inventory را می‌سنجند، نه behavior/runtime محصول. |
| `backend` | وابستگی‌ها با constraints؛ Ruff مجموعهٔ blocker و `ruff format --check`; `scripts/coverage_run.sh` و آستانهٔ per-directory؛ Bandit, `pip-audit`, Semgrep project و harness. اجرای کامل `ruff check .` در job فعلی `continue-on-error` است؛ نتیجهٔ آن blocker اصلی نیست. |
| `studio` | Node 22، install، ESLint، Vitest و Vite build. `npm audit` در workflow طوری تنظیم شده که findingهای غیرcritical لزوماً job را fail نکنند؛ status دقیق audit را هم بخوانید. |
| `client-flutter` | analyze با infoهای غیرکشنده، `flutter test`، manifest gate و گزارش تشخیصی. SDK stable در این job شناور است. |
| `client-pinned` | Flutter 3.50.0 و تطبیق version/revision با devcontainer؛ analyze، test+coverage، Android **debug** APK compile و `dart format` gate. Debug build، signed release APK یا QA دستگاه نیست. |
| `live-contract` | Studio TypeScript client علیه Uvicorn/FastAPI واقعی در SQLite/test fixtures, seed ساختگی و access token آزمونی؛ contract smoke است نه production/network provider. |
| `e2e-api` | Integration testهای Backend؛ محیط آزمون repository است، نه سرویس بانکی/SMS/device production. |

فایل‌های workflow جدا:

- `web.yml`: دستی؛ Flutter Web را analyze/test/build می‌کند و artifact می‌دهد. وجود build artifact با React PWA یکی نیست.
- `container.yml`: push image به GHCR با tagهای full SHA و version در push tag معتبر یا dispatch.
- `deploy.yml`: dispatch دستی، preflight branch default، environment `staging`/`production`, secret webhook/URL و readiness check؛ ساخت/deploy بیرونی نیازمند تنظیم عملیاتی است.
- `client-format-fix.yml`, `gitleaks-fingerprints.yml`, `pwa00-doc-quality.yml`: workflowهای تخصصی/کمکی؛ تریگر/دسترسی‌شان را پیش از استفادهٔ واقعی بخوانید.

هیچ‌یک از pipelineها را «سبز» فرض نکنید: این راهنما GitHub Actions را در همین نوبت query نکرده و build/test محلی هم اجرا نشده است. نتیجه باید با run ID و دقیقاً همان SHA نسبت داده شود.

## ۴.۴ Docker/استقرار و گیت‌های عملیاتی

دو Compose deployment موجود **گزینهٔ جایگزین** هستند و نباید ناخواسته روی یک دیتابیس/volume مشترک هم‌زمان راه‌اندازی شوند:

| مسیر | توپولوژی فایل | آنچه ثابت نمی‌شود |
|---|---|---|
| `mp-app/deploy/docker-compose.yml` | API داخلی، Studio/Nginx روی loopback پورت 8080، Valkey و backup؛ به reverse proxy/TLS بیرونی نیاز دارد. | نصب TLS/DNS/host، امن‌بودن `.env`, backup بیرون میزبان یا اتصال worker. |
| `mp-app/infra/docker-compose.yml` | API internal، Caddy برای ورودی 80/443، Studio، Valkey و Prometheus/exporter/backup. | DNS/public certificate/firewall، secret manager، Alertmanager receiver، registry access یا restore واقعی. |

خود فایل‌های Compose/Dockerfile به‌تنهایی استقرار نیستند. `docs/MuscleParadise/DEPLOYMENT.md`, `OPS-RUNBOOK.md` و `RELEASE-CHECKLIST.md` runbookهای مرجع‌اند، اما در checkout بررسی‌شده بین بخشی از دستورهای آن‌ها و config فعلی اختلاف وجود دارد (مثلاً `zarinpal` در deployment doc، در حالی که `Settings.payment_gateway` فعلاً فقط `manual`, `mock`, `sandbox` می‌پذیرد). تا حل این ناسازگاری، از دستورات production پرداخت آن اسناد کورکورانه پیروی نکنید؛ جزئیات/شواهد در [اختلاف مستندات](05-security-status-glossary.md) آمده است.

### Backup امن برای تمرین روی scratch

`mp-app/backend/scripts/backup.py` را فقط روی دادهٔ ساختگی/scratch اجرا کنید. نمونه‌های زیر مسیر scratch دارند و عمداً به DB واقعی اشاره نمی‌کنند:

```bash
set -euo pipefail
cd mp-app/backend
SCRATCH_ROOT="$(mktemp -d /tmp/mp-backup-drill.XXXXXX)"
DB_PATH="$SCRATCH_ROOT/mp-scratch.db"
export DB_PATH
BACKUP_DIR="$SCRATCH_ROOT/backups"
RESTORE_ROOT="$SCRATCH_ROOT/restore"
python - <<'PY'
import os
import sqlite3
with sqlite3.connect(os.environ["DB_PATH"]) as db:
    db.execute("CREATE TABLE scratch_probe (id INTEGER PRIMARY KEY)")
PY
python scripts/backup.py backup --db "$DB_PATH" --out "$BACKUP_DIR"
ARCHIVE="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.tar.gz' -print -quit)"
test -n "$ARCHIVE"
python scripts/backup.py verify "$ARCHIVE"
python scripts/backup.py restore "$ARCHIVE" \\
  --db "$RESTORE_ROOT/mp.db" --extras-to "$RESTORE_ROOT/extras"
```

`verify` برای بررسی manifest/hash/integrity check طراحی شده و بدون restore است. `restore` ممکن است فایل DB و extras بنویسد؛ فقط روی مسیر خالی و scratch اجرا شود، همیشه `--extras-to` بدهید و مسیرهای `var/receipts`/دادهٔ واقعی را لمس نکنید. backup volume محلی روی همان host disaster recovery نیست؛ offsite encryption/retention، restore drill، RPO/RTO و دسترسی عملیاتی گیت‌های بیرونی هستند.

## ۴.۵ Observability و مواردی که باید پیش از Go/No-Go ثابت شوند

- `GET /health`: liveness سطحی.
- `GET /api/v1/health/ready`: readiness dependencyها؛ پاسخ `ready=true` و HTTP 200 باید از deployment هدف بررسی شود.
- `GET /api/v1/metrics`: token Bearer لازم دارد؛ scrape و alert receiver باید با دادهٔ test شوند.
- rate-limit store مشترک، pool DB، worker heartbeat، outbox pending/dead letter و log correlation باید با deployment واقعی سنجیده شوند.
- production secrets، HTTPS CORS origins، `MP_TRUSTED_PROXIES`, Valkey reachable، SMS واقعیِ approved، payment mode سازگار با تصمیم مالک، DB/migration/backup و registry/image pin باید پیش از هر استفاده از دادهٔ واقعی تأیید شوند.
- OTP dev echo در production ممنوع است؛ code/token/secret را در report/console/chat/screenshot نیاورید.
- Android debug compile در CI signed release نیست. `RELEASE-CHECKLIST.md` گیت‌هایی دربارهٔ signing key تاریخی، Gitleaks history، manifest/API، backup, staging و ops دارد؛ `ADR-007` می‌گوید تا تکمیل flowها و گیت‌ها NO-GO.

## ۴.۶ کارهایی که این سند/نوبت انجام نداده است

- `pytest`, Vitest, Flutter test/analyze/build، Ruff، Bandit، pip/npm audit یا Semgrep اجرا نشده‌اند.
- Alembic روی DB تولید یا scratch upgrade اجرا نشده است.
- جریان `backup`/`verify`/`restore` فقط با DB ساختگی در `/tmp` تمرین شد؛ Docker Compose، Caddy، Nginx، Valkey، Prometheus، restore عملیاتی/production یا deploy workflow اجرا نشده‌اند.
- SMS provider، payment provider/merchant، push, AI inference, camera/QR device و PWA installability تست نشده‌اند.
- این راهنما هیچ secret یا receipt خصوصی را نمی‌خواند/منتشر نمی‌کند و مجوز اجرای release/deploy نمی‌دهد.

# گزارش اجرای ممیزی MP

> ثبت هر بستهٔ کاری (WP). قالب: بازتولید → ریشه → تغییر → تست → شاهد بعد → گیت.

## خط پایه (WP 0.1 بخشی)

- `pytest -q` در `mp-app/backend` (قبل از تغییرات این نشست): **۱۰۹۵ passed، ۲ skipped** در ۲۸۹٫۵۳ ثانیه. خروجی: `/tmp/baseline-pytest.txt` (بیرون از مخزن).
- تعداد عملیات OpenAPI: **۱۴۱ مسیر، ۱۶۳ عملیات**.

## WP 0.3 · F-13 · گارد تکراری روی `POST /axis-assessments/{id}/review`

- **بازتولید:** `tests/integration/test_wp03_axis_single_guard.py` قبل از اصلاح ⇒ `گارد مجوز برای یک درخواست 2 بار اجرا شد` (assert 2 == 1).
- **ریشه:** `mp-app/backend/modules/axis_assessment/router.py:49` — پارامتر `user: Annotated[User, Depends(require_permission())]` در کنار `dependencies=[Depends(require_permission())]` روی روتر (خط ۱۷).
- **تغییر:** پارامتر به `user: CurrentUser` تغییر کرد؛ importهای بی‌مصرف `Annotated` و `User` حذف شدند. (۳ خط، جایگزینی ۲ خط + حذف ۲ import)
- **تست‌های اضافه:** ۲ — `test_review_route_runs_permission_guard_exactly_once`، `test_no_route_has_same_kind_guard_twice`.
- **شاهد بعد:** `test_wp03…` + `test_axis_assessment_api.py` + `test_route_guard_gate.py` ⇒ **13 passed**؛ شمارش گارد هم‌نوع تکراری در کل اپ ⇒ **۰**.
- **گیت عددی:** `enforce` به‌ازای درخواست review: ۲ ⇒ ۱ ✅
- **یادداشت دامنه:** ۱۹ مسیر دیگر دو گارد دارند، ولی هم‌نوع نیستند (`permission` روی روتر + `grant:*` روی مسیر، مثلاً `payments/*` و `expenses/*`). این عمدی است و تغییر داده نشد.
- **آرتیفکت:** `mp-app/backend/api/routes.json` با `scripts/export_routes.py` بازسازی شد؛ تنها تغییر: حذف یک `permission` تکراری از عملیات review (`git diff`: ۱ خط). تست `test_routes_artifact_records_access_matrix` قبل از این بازسازی شکست خورد (artifact کهنه) و بعدش سبز شد.
- **اجرای کامل pytest پس از بازسازی آرتیفکت:** 1097 passed, 2 skipped, 38 warnings in 298.26s (0:04:58) (خام: `/tmp/after-wp03-pytest-2.txt`).
- **ریسک:** رفتار مجوز تغییر نکرد؛ همان `require_permission()` روی روتر همچنان اجرا می‌شود.

## WP 0.6 · F-24 · ثابت منسوخ HTTP 422

- **بازتولید:** `StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated` در `tests/integration/test_unhandled_errors.py`.
- **ریشه:** `mp-app/backend/app/errors.py:72`.
- **تغییر:** ثابت به `HTTP_422_UNPROCESSABLE_CONTENT` (۱ خط).
- **شاهد بعد:** همان تست ۱۶ پاس؛ هشدار 422 دیگر ظاهر نمی‌شود. ruff check و format سبز.
- **باقی‌مانده:** هشدارهای httpx در TestClient و `asyncio_default_fixture_loop_scope` (ابزار تست، نه کد محصول).

## WP 0.5 · F-10 · ESLint استودیو

- **بازتولید:** `npx eslint .` (ESLint 9.39.5) قبل از تغییر ⇒ **۴۲ خطا، ۵ هشدار**. شامل: no-undef برای globalهای Node/SW در `electron/*.cjs` و `public/sw.js` (۲۳)، label-has-associated-control (۱۲)، no-require-imports در تست‌ها (۲)، no-unused-vars، no-autofocus (۱)، و یک eslint-disable بی‌مصرف.
- **ریشه:** نبود `eslint.config` در استودیو؛ اسکریپت `eslint src --ext` با ESLint 9 کار نمی‌کند، و سه نوع globals/تنظیم اشتباه.
- **تغییرات:**
  - `mp-app/studio/eslint.config.mjs` (جدید) — همان flat config بریف با globals مناسب هر فایل و `controlComponents` برای کنترل‌های antd.
  - `package.json`: `lint` = `eslint .`؛ devDependencies: eslint@9، @eslint/js، typescript-eslint، eslint-plugin-react-hooks، eslint-plugin-jsx-a11y، globals.
  - اصلاح کد: `CouponPanel.tsx` (eslint-disable بی‌مصرف)، `PaymentPanel.tsx` (import بی‌مصرف)، `Members.tsx` (ثابت بی‌مصرف)، `PhoneChangeDialog.tsx` (autoFocus ⇒ فوکوس ref با effect)، `public/sw.js` (پارامتر بی‌مصرف)، تست‌ها (require ⇒ import؛ متغیرهای بی‌مصرف).
  - `.github/workflows/ci.yml`: گام «Lint» در job استودیو، پیش از تست.
- **شاهد بعد:** `npx eslint .` ⇒ **۰ خطا، ۰ هشدار** (exit 0). `tsc -b` ⇒ exit 0. `vitest run` ⇒ **۲۸۲ پاس، ۹ skip** (با خط پایه برابر). `vite build` ⇒ موفق.
- **تصمیم:** autoFocus حذف شد و فوکوس با ref در مرحلهٔ کد انجام می‌شود. رفتار کاربر تقریباً همان است، و قاعدهٔ دسترس‌پذیری نقض نمی‌شود. (ثبت در DECISIONS در مرحلهٔ بعدی.)
- **ریسک:** کمترین ریسک؛ تغییر کد فقط در حد import/متغیر بی‌مصرف و یک فوکوس.

## WP 0.8 · A5 · پین SHA برای GitHub Actions

- **بازتولید:** `grep -rhE "uses:" .github/workflows` ⇒ ۴۲ ارجاع، همه با تگ متحرک (`@v4`/`@v2`/`@v6`/`@v3`/`@v5`)، صفر پین‌شده.
- **تعداد یکتا:** ۷ ارجاع (checkout@v4 ×۱۷، flutter-action@v2 ×۶، upload-artifact@v4 ×۶، build-push-action@v6 ×۴، setup-python@v5 ×۴، setup-node@v4 ×۳، login-action@v3 ×۲).
- **روش:** SHA هر تگ از `gh api repos/<o>/<r>/commits/<tag>` (api.github.com) گرفته شد؛ هر خط به `@<40-hex> # <tag>` تبدیل شد.
- **شاهد بعد:** ۴۲/۴۲ پین‌شده (`grep ... | grep -vE "@[0-9a-f]{40}"` ⇒ ۰)؛ YAML همهٔ workflowها با PyYAML parse می‌شود.
- **ریسک:** اگر یکی از SHAها بعداً حذف شود، CI شکست می‌خورد؛ به‌روزرسانی با `pin-github-action` یا Renovate انجام می‌شود (ابزار به‌روزرسانی در مرحلهٔ بعد).

### تکمیل WP 0.8: تست‌ها

- `test_deploy_workflow_is_manual_and_pushes_sha_tagged_images` پس از پین شدن `uses:` شکست خورد (تطبیق رشتهٔ `@v6`). تست به تطبیق با نام action اصلاح شد؛ معیار تست تضعیف نشد.
- تست گیت جدید `test_every_github_action_is_pinned_to_commit_sha` اضافه شد (ارجاع بدون SHA ⇒ شکست؛ با جدا کردن نمونهٔ `@v4` تأیید شد).
- **pytest کامل:** ۱۰۹۸ passed، ۲ skipped، ۲ warning (قبل: ۳۸ warning)، خروجی صفر.

## WP 1.3 · F-06 / A2 · `/api/v1/metrics` بدون احراز هویت

- **بازتولید (قبل):** `mp-app/backend/api/v1/monitoring.py:14` بدون dependency؛ `api/routes.json` guard را `—` ثبت کرده بود؛ `route_guard_gate.PUBLIC` این مسیر را «عمومی» نگه داشته بود. (شاهد بیرونی بریف: ۲۰۰ بدون توکن، ۳۴۶ خط، ۱۲ خانوادهٔ متریک.)
- **تصمیم (D-؟ — ثبت در DECISIONS در مرحلهٔ بعد):** Bearer با `MP_METRICS_TOKEN` در اپ، نه فقط Caddy. دلیل: دفاع عمق؛ گزینهٔ «فقط Caddy» رد شد چون حفاظت را به یک لایه می‌سپارد. توکن خالی = بسته (۴۰۳) — پیش‌فرض ایمن.
- **تغییرات:**
  - `app/config.py`: `metrics_token` (MP_METRICS_TOKEN).
  - `api/v1/monitoring.py`: `require_metrics_token` با `hmac.compare_digest` و `__rbac__="metrics_token"`.
  - `scripts/route_guard_gate.py`: حذف دو ورودی `/api/v1/metrics` از PUBLIC.
  - `scripts/dast.py`: حذف `/api/v1/metrics` از فهرست عمومی مورد انتظار (حالا باید ۲xx ندهد).
  - `infra/Caddyfile`: `handle /api/v1/metrics { respond 404 }` پیش از `/api/*`.
  - `infra/docker-compose.yml`: `MP_METRICS_TOKEN` برای backend و prometheus با `:?` (الزامی).
  - `infra/monitoring/prometheus.yml`: `authorization: Bearer credentials: ${MP_METRICS_TOKEN}`.
  - `api/routes.json`: بازسازی شد (۸ خط؛ guard متریک حالا `metrics_token`).
  - تست‌ها: فیکسچر autouse توکن در `tests/integration/conftest.py`، ثابت‌ها در `tests/integration/_metrics.py`، هدر در ۶ فراخوانی `/metrics`.
  - مستندات: `OPS-RUNBOOK.md`، `DEPLOYMENT.md`.
- **تست‌های جدید:** `tests/integration/test_wp13_metrics_auth.py` (۶ تست: بدون توکن ۴۰۱، توکن غلط ۴۰۱، scheme غلط ۴۰۱، توکن درست ۲۰۰، توکن خالی ۴۰۳، گیت guard ثبت‌شده).
- **شاهد بعد:** ۴۴ تست مرتبط پاس؛ artifact و ماتریس دسترسی ۲۶۷ پاس.
- **باقی‌مانده:** اعتبارسنجی `MP_METRICS_TOKEN` در `validate_production_configuration` (در WP 4.1 با بقیهٔ کلیدها)؛ اجرای واقعی Prometheus با Compose (BLOCKED: Docker در این محیط نیست).

- **pytest کامل پس از WP 1.3:** ۱۱۰۴ passed، ۲ skipped، ۲ warning، خروجی صفر (`/tmp/after-wp13-pytest.txt`).

## WP 1.1 · F-01 · اعتماد به X-Forwarded-For فقط از پروکسی معتمد

- **بازتولید:** `tests/regression/test_wp11_xff_trust.py` با uvicorn زنده و فلگ‌های قبلی (`--forwarded-allow-ips='*'`) ⇒ `[200 × 30]`؛ یعنی هر ۳۰ درخواست با XFF جعلی از peer نامعتمد پذیرفته می‌شد.
- **ریشه:** `mp-app/backend/Dockerfile:27` و `mp-app/infra/Dockerfile.backend:29`: uvicorn همهٔ peerها را معتمد می‌کرد، پس `request.client` پیش از اپ از هدر جعلی پر می‌شد.
- **تغییرات:** `scripts/uvicorn_proxy_flags.sh` (جدید، ۱۰ خط)؛ هر دو Dockerfile از آن استفاده می‌کنند؛ `app/config.py` (اعتبارسنجی `MP_TRUSTED_PROXIES` در production)؛ `infra/docker-compose.yml` (+۲)؛ `docs/MuscleParadise/DEPLOYMENT.md`؛ `tests/regression/test_production_ops.py` (فیکسچر production یک مقدار معتبر گرفت).
- **تست‌های اضافه:** `test_wp11_xff_trust.py` — ۱۳ مورد (۵ اعتبارسنجی، ۲ Dockerfile، ۲ فلگ، ۱ compose، ۱ e2e زنده با ۳۰ درخواست).
- **شاهد بعد از اصلاح:** `pytest tests/regression/test_wp11_xff_trust.py` ⇒ ۱۳ passed؛ همان e2e با فلگ قدیمی ⇒ ۱ failed (`[200×30]`)، پس تست واقعاً نقص را می‌گیرد.
- **گیت عددی:** ≥۲۷ × 429 از ۳۰ ⇒ PASS (شاهد: ۲۷+ ۴۲۹).
- **کنترل‌نشده / باقی‌مانده:** متریک `mp_rate_limit_key_source{peer|xff}` هنوز اضافه نشده (بخش بریف). وضعیت: **FIXED-PARTIAL**.

## WP 1.2 · F-02 · محیط fail-safe و dev_code دوشرطی (BD-3)

- **بازتولید:** پیش از اصلاح، `POST /api/v1/auth/otp/request` در محیط بدون `MP_ENVIRONMENT` پاسخ `dev_code` می‌داد (`modules/auth/service.py:53` و `:261` بدون شرط محیط جز `provider.name=="dev"`).
- **ریشه:** `app/config.py` پیش‌فرض `environment="development"`؛ `MP_SMS_PROVIDER` پیش‌فرض `dev`؛ هیچ گیت شروع وجود نداشت.
- **تغییرات:** `app/config.py` (`allow_dev_otp_echo`، `allow_implicit_dev`، رد echo در production)؛ `app/main.py` (`_assert_explicit_environment`، `_log_effective_configuration` با WARNING)؛ `modules/auth/service.py` (`dev_otp_echo_enabled`)؛ `modules/auth/router.py` (`response_model_exclude_none` برای دو مسیر OTP)؛ `scripts/deploy_gate.py` (`check_otp_echo_guard`، `otp_body_exposes_dev_code`)؛ `tests/conftest.py` (`MP_ALLOW_IMPLICIT_DEV` و فیکسچر `dev_otp_echo`)؛ پنج ماژول تست OTP با `pytestmark` opt-in؛ `test_sms.py` (بازنویسی تست قدیمی‌ای که پیش‌فرض را مجاز می‌دانست).
- **ابزارهای اصلاح‌شده:** `scripts/route_guard_gate.py`، `scripts/export_routes.py`، `scripts/dast.py` و `scripts/build_audit_inventory.py` (`setdefault("MP_ENVIRONMENT","development")` برای ابزار فقط‌خواندنی).
- **تست‌های اضافه:** `tests/regression/test_wp12_env_failsafe.py` — ۱۰ مورد (پاسخ بدون کد، پاسخ با پرچم، guard در منبع، شروع بدون محیط، شروع با محیط صریح، محیط از env، رد echo در production، پذیرش production بدون echo، گیت روی مخزن، تشخیص بدنه).
- **شاهد بعد از اصلاح:** `deploy_gate.py` ⇒ ۱۴ بررسی، ۰ مشکل، خروجی صفر؛ `route_guard_gate.py` ⇒ خروجی صفر، ۱۶۳ مسیر، ۱۵۵ دارای guard؛ `pytest` کامل ⇒ **۱۱۲۸ passed، ۲ skipped، خروجی صفر** (`/tmp/after-wp11-12-pytest.txt`).
- **یادداشت صادقانه:** تست‌های «شروع بدون محیط» همراه پیاده‌سازی نوشته شدند نه قبل از آن (قرمزِ اول فقط برای `dev_code` و شمارش منبع دیده شد). تأیید red برای این دو مورد انجام نشده؛ در WP بعدی با حذف موقت guard بازتولید می‌شود.
- **گیت زنده (`curl` روی استقرار):** عمداً پیاده‌سازی نشد؛ هر درخواست OTP به شماره ناشناس SMS واقعی می‌فرستد. جایگزین: گیت استاتیک + `otp_body_exposes_dev_code` روی پاسخ‌های واقعی در استقرار (BLOCKED تا محیط استقرار). وضعیت: **FIXED-PARTIAL**.

## نگهداری ابزارهای ممیزی (WP 1.1–1.2)

- `scripts/build_audit_inventory.py --check` پس از ایجاد فایل‌های جدید باید کامیت شده باشد: این گیت از `git ls-files` استفاده می‌کند، پس قبل از کامیت «کهنه» می‌دهد. `INVENTORY.md` پس از کامیت دوباره ساخته و بررسی شد.
- مشکل میانی: اسکریپت فهرست بدون متغیر محیط، بخش OpenAPI (۱۶۳ عملیات) را حذف کرد؛ با `setdefault` در کد subprocess اصلاح شد. این مورد به‌عنوان تله ثبت شد.

## WP 1.4 · F-08 · خروج از همه و توکن‌های بی‌sid (BD-6)

- **بازتولید:** `tests/integration/test_wp14_logout_all.py` پیش از اصلاح ⇒ `assert 200 == 401` برای توکن بی‌sid/بی‌ver پس از `POST /auth/logout-all`؛ و `seed_s3c_m39.py` ⇒ `print(f"{token}|{member.id}")` در تست نشت‌توکن قرمز.
- **ریشه:** `modules/auth/service.py::logout_all` فقط refreshها را revoke می‌کرد؛ `app/deps.py` برای tokenهای بی‌`sid` فقط نسخهٔ `ver` را می‌سنجید و `ver` قدیمی‌ها را هم کاربر فعال تلقی می‌کرد.
- **تغییرات:** `modules/auth/service.py` (bump `auth_version`)؛ `scripts/dast.py` (`_token` با RefreshToken و sid واقعی)؛ `scripts/seed_s3c_m39.py` (توکن به فایل 0600 با `MP_SEED_TOKEN_FILE`، stdout فقط member_id)؛ `tests/regression/test_wp12_env_failsafe.py` (پاک‌سازی `MP_ENVIRONMENT` در تست‌های محیط).
- **تست‌های اضافه:** `tests/integration/test_wp14_logout_all.py` — ۴ مورد (توکن بی‌sid ⇒ ۴۰۱، توکن OTP ⇒ ۴۰۱، ورود تازه پس از logout-all ⇒ ۲۰۰، نبود چاپ توکن در ابزارها).
- **شاهد بعد از اصلاح:** `pytest tests/integration/test_wp14_logout_all.py` ⇒ ۴ passed (پس از اصلاح)؛ ماژول‌های auth/session/rbac ⇒ ۹۱ passed؛ **pytest کامل ⇒ 1132 passed، 2 skipped، خروجی صفر** (`/tmp/after-wp14-pytest.txt`).
- **خطای میانی:** تست «شروع بدون محیط» در اجرای کامل شکست خورد چون متغیر `MP_ENVIRONMENT` از تست قبلی به فرایند نشت می‌کرد؛ تست اکنون متغیر را خودش پاک می‌کند. ثبت به‌عنوان تله: تست‌های پیکربندی باید محیط خودشان را کنترل کنند.
- **گیت عددی:** توکن بی‌sid پس از logout-all = ۴۰۱ ⇒ PASS.
- **باقی‌مانده:** قاعدهٔ Semgrep «`create_access_token(` بدون `session_id=` خارج از تست» به WP 0.7/4.7 منتقل شد. وضعیت F-08: **FIXED-PARTIAL**.

## الحاقیهٔ A1 · ثبت خط پایه (قبل از هر تغییر) و یافته‌های F-28 و F-29

- **قبل (اندازه‌گیری‌شده روی 662ff88، ruff 0.17.6):** `ruff check .` = All checks passed (exit 0، ۵۲–۵۸ ms)؛ `ruff check --select ALL .` = ۱۱٬۷۷۸ یافته (exit 1، ۲۹۶ ms)؛ `ruff format --check .` = ۳۷۸ فایل پیش‌تر قالب‌بندی‌شده. جدول کامل و اختلاف‌ها در `BASELINE.md`.
- **تأیید یافته‌ها:** `TRY400`×۶ در `app/sms.py` (F‑29)؛ `DTZ011`×۳ و `DTZ001`×۱ (F‑28)؛ `C901` بدترین ۲۸ در `app/config.py:128` (F‑15)؛ `ERA001`×۱۱ همه کامنت فارسی.
- **اختلاف‌ها:** `RUF100` = ۷۲ (نه ۳۹)؛ قاعده‌های `ALL` = ۱۰۴ (نه ۱۰۸)؛ `S105` = ۳ (نه ۴)؛ `ruff-recommended.toml` در مخزن نیست و باید بازسازی شود. این اختلاف‌ها در `BASELINE.md` بخش ج ثبت شده‌اند.
- **تغییر در این مرحله:** `findings.json` (F‑28، F‑29)، `status.json` (هر دو OPEN)، `scripts/build_audit_inventory.py` (شمارش ۲۹)، `BASELINE.md` (جدید، بخشی)، `DECISIONS.md` (AD‑1، AD‑2). هیچ کد محصولی تغییر نکرد.
- **باقی‌مانده:** WP 0.9، WP 2.6، WP 3.6 و بازنگری WP 4.5 در صف `FINN-AUDIT-LOOP.md`؛ هنوز اجرا نشده‌اند.
- **یادداشت محیطی:** در این نشست، فضای `/tmp` (venv و بستهٔ ممیزی) بازنشانی شده بود؛ شاخهٔ محلی روی `662ff88` قرار داشت و کامیت‌های ممیزی فقط روی remote بودند. با `git reset --mixed origin/arena/da474b65-mp` همگام شد؛ پیش از آن، هر ۷۵ فایل تغییریافته/بی‌ردیابی بایت‌به‌بایت با remote برابر بودند (هیچ کاری از دست نرفت).

### A1.1 · اصلاحیه و نگاشت نام‌ها

- **نگاشت:** AD‑1 ≡ D‑6 و AD‑2 ≡ D‑7 در الحاقیهٔ A1 (نام‌گذاری AD به‌خاطر اشغال بودن D‑6/D‑7 در این مخزن).
- **تأیید مستقل روی base 662ff88:** ۱۰۴ قاعدهٔ متمایز؛ S105=۳ + S106=۱؛ `log.error` در ۶ محل داخل `except`؛ ERA001=۱۱.
- **تصحیح:** RUF100 = ۳۹ ادعا تأیید نشد (`--select`=۷۲؛ `--extend-select` روی پیکربندی فعلی=۵۹)؛ عدد ۳۹ وابسته به ruff-recommended است.
- **مانع WP 0.9 (مرحلهٔ ۱):** `ruff-recommended.toml` در مخزن نیست و متن آن در A1.1 §۲‑الف در پیام دریافتی وجود ندارد. تا دریافت آن هیچ پیکربندی ruff تغییر نکرد.

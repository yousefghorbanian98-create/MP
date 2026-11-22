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

## A1.3 · WP 0.9 (گام‌های ۱–۵) — رکورد اجرای بی‌ناظر

- **برچسب:** addendum A1.3 · **نگاشت:** AD‑3 (مبنای گیت)، AD‑4 (CI)، AD‑5 (S608/کامنت). AD‑1≡D‑6، AD‑2≡D‑7 (قبلاً ثبت شد).
- **پیش‌نیاز:** متن ruff-recommended در A1.3 §۵ دریافت شد؛ sha256 `6bafdba17d60db628197cf89aa4c65477025e0207bc3e1612612f2c2cdf72e5a` تطبیق داده شد (۴٬۹۷۳ بایت).

### گام ۱ — پیکربندی (`5d820a0`)
- فرمان: `pyproject.toml` بلوک `[tool.ruff]` با همان متن §۵ جایگزین شد (با سرآیندهای `[tool.ruff.lint]`)؛ `known-first-party` حفظ شد.
- گیت: `RUFF=/tmp/venv/bin/ruff ./verify-addendum-gates.sh before` روی **662ff88** ⇒ `کل یافته 430 MATCH · قواعد 52 MATCH · RUF100 39 MATCH · TRY400 6 · DTZ011 3 · format 0 · ۲۰ noqa 20 · S608 4` ⇒ **PASS**.
- روی HEAD (پیش از رفع): ۴۴۰ / ۴۰ RUF100 / ۱۲ از ۲۰ noqa (**جابه‌جایی خط**، نه حذف؛ شمارش به‌ازای فایل شد) ⇒ AD‑3.

### گام ۲ — ERA001 به ignore (`e335653`)
- فرمان: افزودن `"ERA001"` با دلیل فارسی به `ignore`.
- گیت: `stage=after-era` روی **662ff88** ⇒ `419 MATCH · 51 MATCH · RUF100 39 · ۲۰ noqa 20 · S608 4` ⇒ **PASS**.
- یادداشت: `ruff check --select ERA001` هنوز ۱۱ می‌دهد؛ این طبیعی است چون `--select` روی CLI ignore را دور می‌زند.

### گام ۳ — ترتیب F‑22 و RUF100 (تصحیح روش)
- **اشتباه من، اصلاح‌شده:** اولین dry-run با `--select RUF100` ⇒ ۶۹ (نادرست؛ `--select` بقیه را خاموش می‌کند). با پیکربندی کامل و فیلتر `RUF100` ⇒ **۴۰** روی HEAD، که ۴ تا در migration و ۳۶ قابل حذف‌اند. dry-run‌ها فقط `--diff` بودند؛ `git status` بعدش تمیز ماند.
- ترتیب اجرا: `ruff check --fix --exclude db/migrations/versions/c3f01ab129e2_*.py` ⇒ `45 fixed` (ایمن)؛ migration بدون تغییر؛ ۴ `noqa: S608` باقی.

### گام ۴ — رفع‌های ایمن (`9868a11`)
- شامل: ۳۶ RUF100 (ـ بدون noqa بلااثر)، RUF022 (ترتیب `__all__`)، FURB110 (`a if a else b → a or b`؛ معادل)، FURB167، RUF021.
- کامنت دلیل‌دار `test_m46_db_pool.py:33` به‌صورت کامنت ساده حفظ شد.
- **اشتباه کمکی (اصلاح‌شده، قبل از push):** `git add -A` ۱۴ PNG آزمایشی `var/receipts/` را هم staged کرد؛ commit بازنویسی شد؛ PNGهای untracked آزمایشی پاک شدند (۷۵ tracked دست‌نخورده).
- `ruff check .` ⇒ `384 errors` (شامل migration)؛ `ruff format --check .` ⇒ `385 files already formatted`.
- pytest: `1132 passed, 2 skipped, 2 warnings in 308.04s` ⇒ **exit 0** (پایهٔ WP 1.4 همین بود).

### گام ۵ — CI و پین ruff (`07f096d`)
- `.github/workflows/ci.yml`: مرحلهٔ بلوکینگ `ruff check --select E,F,W,I,N,UP,B,SIM --ignore E501 .` + `ruff format --check .` (⇒ exit 0)؛ مرحلهٔ کامل `continue-on-error: true`.
- `pyproject.toml`: `ruff>=0.3` ⇒ `ruff==0.17.6`.
- YAML با PyYAML بارگذاری شد (`ok`) — پس از رفع خطای نام مرحله (`: ` در scalar بدون نقل‌قول).

### تأیید نهایی
- **انحراف از سند:** (۱) گیت مطلق روی base (AD‑3)؛ (۲) ۴۵ به‌جای ۴۷ رفع ایمن (AD‑5)؛ (۳) CI زیرمجموعهٔ بلوکینگ به‌جای «S بلوکینگ» (AD‑4، چون S هنوز ۴۰ یافته دارد)؛ (۴) `RUF100 = 0` پس از ۲.۶ به‌جای `0` در جدول: صفر فقط پس از WP 4.5 ممکن است (AD‑5).
- **HARD-STOP برخورد‌شده:** هیچ. (`ruff --fix --unsafe-fixes` اجرا نشد؛ هیچ migration تغییر نکرد؛ هیچ ignore/per-file-ignore جز ERA001 اضافه نشد.)
- **فایل `share/MP-BUILDER-HANDOFF-A1.3.md`:** در این مخزن وجود ندارد (`share/` نیست)؛ شناسهٔ `bce286e` روی `arena/2cde32d6-chat2db` است، نه شاخهٔ من؛ به آن شاخه سوئیچ نکردم.
- **/tmp/venv:** دوباره ساخته شد (ruff 0.17.6، `pip install -e .[dev]`)؛ هر شاهد در مخزن ثبت شده است.
- **باقی‌مانده:** WP 2.6 (F‑29)، WP 3.6 (F‑28)، WP 4.5 (F‑22)، گیت نهایی و گزارش ۲۹ یافته (§۳‑۷) — **NOT-STARTED**.

## WP 2.6 و WP 3.6 — ریز‑حلقه‌ها (الحاقیهٔ A1)

### WP 2.6 (F‑29) — کامیت `95b1a44`، شاخص `3cce4d5`
- **red:** `tests/regression/test_wp26_sms_logging.py` روی کد قبل: ۶ تست exc_info ناموفق؛ ۸ تست دیگر (نشت کلید، رد https) از قبل سبز بودند ⇒ به‌عنوان گارد ثبت شد، نه اصلاح.
- **انحراف:** `log.exception` مستقیم کلید Kavenegar را از متن استثنا نشت می‌داد (تست موجود `test_sms::credentials` گرفت) ⇒ helper `_log_provider_failure` و AD‑6.
- **green:** ۱۴ تست جدید + ۶۱ تست sms/security؛ pytest کامل ۱۱۴۶ passed، ۲ skipped، exit 0؛ `after-wp26` PASS.
- **یادداشت:** `build_audit_inventory.py` دو بار اجرا و سپس `--check`؛ نوشتن و خواندن ناهمگون بود، پس از تکرار تا پایداری `INVENTORY` کامیت شد (`3cce4d5`).

### WP 3.6 (F‑28) — این کامیت
- **red:** تست‌ها ابتدا روی کامیت پیش از تغییر (`HEAD` پیش از این WP) اجرا شد: سن `axis` و اسکن `date.today()` و هر دو Dockerfile ناموفق؛ `app.clock` وجود نداشت. نکته: یک بار `app.clock` از نصب editable درخت اصلی خوانده شد و تست ساعت بی‌ارزش سبز شد؛ با جابه‌جایی موقت فایل، red معتبر گرفته شد (`ModuleNotFoundError`) و فایل بازگردانده شد.
- **green:** ۵ تست؛ `after-wp36` PASS (`date.today()` = ۰، DTZ011 = ۰)؛ pytest کامل ۱۱۵۱ passed، ۲ skipped، exit 0.
- **زمان‌بندی تست:** ساعت ۲۰۳۰‑۰۳‑۲۰ ۲۱:۰۰ UTC (= ۰۰:۳۰ تهران ۲۱ مارس). ساعت واقعی ماشین (۲۰۲۶‑۱۱‑۲۱) با نتیجه‌ها تداخل ندارد.
- **پیامد:** `ENV TZ=Asia/Tehran` در `backend/Dockerfile` و `infra/Dockerfile.backend`؛ AD‑1 لایهٔ دوم.

### WP 1.5 (F‑09) — این کامیت
- **red:** `tests/regression/test_wp15_rial_strict.py` روی کد قبل: ۲۳ ناموفق / ۱۰ موفق (موفق‌ها مواردی‌اند که کد قبل همان ورودی را رد می‌کرد، مثل `True` و `'1e6'`، یا تست پذیرش). استودیو: `tests/wp15Money.test.ts` ناموفق با خطای import (`src/lib/money` نبود).
- **تنظیم red:** نمونهٔ اولیه (۱۰^۱۸+۷ با نرخ ۰٫۱) در float و Decimal برابر درآمد؛ با نرخ ۰٫۳ اختلاف دیده شد؛ تست روی همان اصلاح شد.
- **green:** ۳۳ تست بک‌اند؛ ۱۵ تست استودیو؛ vitest کامل ۲۹۸ passed، tsc و eslint صفر.
- **گیت:** `verify-addendum-gates.sh after-wp15` PASS (پیش از این، تعداد فیلدها یک‌بار به‌ازای هر فایل شمرده می‌شد و BLOCKED-NUMERIC می‌داد؛ اصلاح به شمارش خط‌ها، ۵ از ۵).
- **lint:** lint بلوکینگ CI (E,F,W,I,N,UP,B,SIM) و `ruff format --check` صفر. TC001/TC003 جدید در schemaها هم‌الگوی فایل‌های موجود است و در بخش غیربلوکینگ است.
- **pytest کامل:** ۱۱۸۴ passed، ۲ skipped، exit 0 (۳۴۰ ثانیه).
- **پیامد:** AD‑7.

### WP 4.5 (F‑21، F‑22) — این کامیت
- **red (F‑22):** `tests/regression/test_wp45_f22_migration_sql.py` روی کد قبل: ۱ ناموفق (فراخوانی `execute` با SQL ساخته‌شده در migration). آشکارساز روی الگوی `DROP INDEX` سبز بود (تست حفاظتی).
- **کشف مهم — قاعدهٔ semgrep مرده بود:** `mp-raw-sql-string-format` در `.semgrep/project-rules.yml` هرگز روی هیچ فایلی یافته نمی‌داد: (۱) `**/migrations/*` مستثنا بود؛ (۲) الگوها فقط با `, ...` تطبیق می‌یافتند؛ (۳) `pattern-not-inside: def $F(...): ...` هر تابعی را می‌پوشاند. نمونهٔ دیباگ روی فایل نمونه: قبل ۰، بعد ۴ (خطوط مطابق). بعد از repair روی migration دقیقاً ۴ یافته (۶۷/۱۶۵/۱۶۹/۱۷۱) و روی کل backend ۰.
- **green (F‑22):** `_drop_index_if_exists` با inspector و `op.drop_index`؛ ۴ `# noqa: S608` حذف؛ `S608` از ignore مربوط به `db/migrations/**` حذف شد.
- **شاهد زنجیرهٔ migration:** `alembic upgrade head` ⇒ `downgrade f1a2b3c4d5e6` ⇒ `upgrade head` روی SQLite همه exit 0؛ ایندکس‌ها پس از برگشت دوباره ساخته شدند.
- **F‑21:** `hypothesis>=6.100` در extras dev؛ پنج اسکریپت به `with` یکدست شدند (red ۵/۵ ⇒ green ۵/۵). `dast.py --help` exit 0.
- **S family فعال و بلوکینگ:** ۳۷ یافتهٔ S (بیشترشان تست). تست‌ها: ignore با دلیل برای S603/S607/S105/S106. کد واقعی: `monitoring` (S110) و `dast` (S112) با لاگ debug در helper ⇒ `noqa: BLE001` حفظ شد (۲۰ noqa محفوظ). `build_exercise_gifs` assert ⇒ `RuntimeError`. دو S105 مستند با `noqa` (مقدار توسعه و `token_type`). CI blocking: `--select E,F,W,I,N,UP,B,SIM,DTZ,TRY400,S`.
- **TRY به‌صورت کد دقیق:** خانوادهٔ `TRY` در خط فرمان `TRY003` را برمی‌گرداند که در pyproject ignore است؛ پس `TRY400` آمد.
- **خطای کشف‌شده در WP 3.6:** کامیت `3ee7838` یک `I001` در `modules/axis_assessment/service.py` گذاشت که lint بلوکینگ CI را می‌شکست. با safe fix (`--select I001`) اصلاح شد؛ این را ثبت می‌کنم که WP 3.6 گیت lint کامل را اجرا نکرده بود.
- **یادداشت:** `seed_criteria.py --help` exit 1 است، ولی این رفتار قبل از تغییر هم همین بود (اسکریپت آرگومان ندارد و روی DB خالی اجرا می‌شود).
- **گیت:** `verify-addendum-gates.sh after-wp45` PASS (RUF100 = ۰، S608 = ۰، ۲۰ noqa = ۲۰، format = ۰، date.today = ۰).
- **pytest کامل:** ۱۱۹۱ passed، ۲ skipped، exit 0 (۲۹۶ ثانیه). semgrep کل backend: ۰ یافته، ۰ خطا.


## WP 0.1 · ۴۹ ردیف خط پایه و شواهد زنده (HEAD `5188a0d`، base `662ff88`)
- **بازیابی سند بازتولید:** `MP-REPLICATION-2026-11-21.md` از شاخهٔ کیت (`handoff/`) گرفته شد؛ sha256 `6a7a71ef…` تطبیق داده شد.
- **پراب‌ها روی S3 (فرمان Dockerfile، ۲ ورکر، `MP_ALLOW_DEV_OTP_ECHO=true`):** `probe_contract seed/matrix/invalid` exit 0؛ `probe_invalid_authed` exit 0؛ `probe_live_security` exit 0؛ `probe_otp_limits all` exit 0؛ `probe_load plain-dev 10 40 60 80` exit 0؛ `probe_load backend-instr 40 80` exit 0؛ `bench_logging` exit 0؛ `repro_rbac_systemerror` exit 0؛ `scan_ui_wiring` exit 0.
- **pytest کامل با پوشش:** `1191 passed، 2 skipped، exit 0` (`PYTEST_RC=0`)؛ پوشش ۸۴٪. `npm ci` در `mp-app/studio`: `NPM_RC=0`.
- **اشتباه‌های اجرا و اصلاح:** (۱) probe ها مسیر `/tmp/run` می‌خواستند ⇒ symlink. (۲) `openapi-live.json` لازم بود ⇒ از `/openapi.json` گرفته شد (۱۴۱ مسیر). (۳) `probe_otp_limits bruteforce` mode ندارد و پاس بی‌خروجی بود ⇒ پراب جدید. (۴) اولین اجرای probe ها بدون `MP_ALLOW_DEV_OTP_ECHO` بود؛ کل اجرا دوباره انجام شد.
- **ابزار تکمیلی:** `knip@5` (exit 1 = یافته، نه کرش)، `madge` exit 0، `jscpd` exit 0، `tsc` exit 0، `vitest` exit 0 (۲۹۸ پاس)، `eslint` exit 0 (۰/۰)، semgrep کیت روی base و HEAD (۱۹ ⇒ ۲)، `pathid` (۶۰/۶۰)، mutmut دستی (۲۶/۴۵).
- **commit:** `mp-app/studio/dist` وجود نداشت؛ `/home/user/MP/share/` (فایل از پیش موجود، بی‌ارتباط) از commit حذف شد.

## WP 0.2 · F‑12 · گاردهای مؤثر در `routes.json` — BLOCKED (گیت باینری کیت قرمز)

WP: 0.2 · F: F‑12 · برچسب: `routes.json` (فیلد guards/roles) ≡ «ماتریس ۱۶۳×۷ ⇒ مشاهده‌شده == اعلام‌شده»
commit: (ثبت‌شده در پیام commit WP 0.2؛ شاخهٔ `arena/da474b65-mp`)

- **پیش‌سنجش:** `git status --porcelain` قبل از شروع: تمیز (جز `share/` از پیش موجود، خارج از commit). `git log -3`: `839500d` (WP 0.1) در HEAD. ورودی کیت: `kit.zip` sha256 `9a192500…` (مطابق). venv `/home/user/audit-run/venv` نصب شد (`INSTALL_RC=0`). دیتابیس محلی: `alembic upgrade head` (rc 0) + `seed_live.py` (rc 0، ۲۵۰ عضو).
- **قرمز (قبل از تغییر):** `pytest tests/integration/test_routes_effective_guards.py` روی artifact قبلی ⇒ `8 failed`. (ابتدا تست نوشته شد، سپس مولد.)
- **ماتریس قبل از تغییر (شاهد خام):** `probe_contract.py all` (کیت، بدون تغییر) ⇒ `unauth_allowed 5`، `over_permissive 2`، `contract_drift_denied 604`، `server_errors 0` (`/tmp/wp02/all-dump.log` ⇒ `evidence/after/wp02/kit-probe/kit-all-before-change.log`). ماتریس تمیز (`scripts/wp02_matrix.py`، ۱ relogin بعد از `logout-all`) ⇒ `cells 1141`، ناهمخوانی باینری روی artifact قبلی: **115** (99 + 15 + 1).
- **علت ۴۰۱ «نشست معتبر نیست»:** ابطال توکن‌ها توسط کال‌های قبلیِ ماتریس (logout/logout-all). اثبات: با توکن تازه `GET /members/me` ⇒ ۲۰۰ برای هر ۷ اصل؛ توکن‌ها `sid` و `ver` دارند. `sid` در کد برای `/auth/sessions` اجباری نیست.
- **اصلاح:** `scripts/export_routes.py` (`effective_access`، `access_matrix`)، `app/security/route_policy.py` (جدید: `SUPER_ADMIN_ONLY` ۱۵، `OWNER_SCOPE` ۳۵، `BODY_CREDENTIAL` ۱، `REQUIRES_BOUND_SESSION` ∅)، `api/routes.json` بازتولید (141 مسیر، 163 عملیات)، `tests/integration/test_routes_access_matrix.py` (منطق جدید + تست عمومی)، `test_routes_effective_guards.py` (جدید).
- **سبز:** `pytest tests/integration/test_routes_effective_guards.py` ⇒ `8 passed`؛ `test_routes_access_matrix` + `test_routes_artifact` + `test_wp03_axis_single_guard` ⇒ `12 passed` (با تست‌های بالا)؛ **پیش از commit، کل بک‌اند:** `1199 passed، 2 skipped، exit 0` (`backend-test-suite-wp-0-2-check`).
- **ruff:** `ruff 0.17.6`؛ `ruff check` روی فایل‌های تغییر‌یافته ⇒ `All checks passed!`؛ `ruff format` روی ۴ فایل اعمال شد؛ `route_guard_gate.py` ⇒ exit 0.
- **گیت‌ها:**
  - ارزیاب سه‌ارزشی (`scripts/wp02_eval.py` روی `matrix-cells-clean.json`) ⇒ `cells 1141`، `exact 915`، `conditional 226` (owner_scope 184، grant 35، body_credential 6، anonymous may 1)، `server_errors 0`، **`mismatch_total 0`**.
  - **کیت `probe_contract.py all` (بعد از تغییر، بدون تغییر کیت):** `unauth_allowed 5` (همه عمومی)، `over_permissive 0`، `contract_drift_denied 592`، `server_errors 0`، `leaked_stacktrace 0`، `slow_ops 0` ⇒ `kit-probe/kit-all-after.log`. گیت باینری کیت **قرمز** است؛ ۶۹ سلول اختلاف باینری همه شرطی‌اند (۶۸ «مجاز اعلام‌شده، ۴۰۳» + ۱ anonymous `may`). ۵۹۲ عدد کیت ترکیبی از ۶۹ شرطی و آلودگی ابطال توکن در همان اجراست؛ ادعای «۰» نمی‌شود.
- **تلاش‌ها (G4، حداکثر ۳):** (۱) تغییر مولد به سیاست مؤثر ⇒ تست‌های قدیمی شکستند و اصلاح شد؛ (۲) ماتریس تمیز با رفع ۴۲۲ کاذب ⇒ ۵ عملیات سرویس‌سطح با body معتبر؛ (۳) تحلیل گیت باینری ⇒ شرطی بودن ذاتی، نه قابل‌سبز‌شدن بدون تغییر گیت یا داده. سه تلاش ⇒ `BLOCKED`.
- **انحراف از سند:** AD‑10 (گیت باینری کیت قرمز؛ مسیرهای عمومی `roles` = همه؛ `requires_bound_session` تهی). کیت و گیت‌ها تغییر نکردند.
- **یافته‌های جدید:** (۱) F‑12 علت `sid` را اشتباه نسبت داد؛ 401 از آلودگی ابطال بود. (۲) `probe_contract.py` ترتیب مسیرها را رعایت می‌کند و خودش کاذب 401 تولید می‌کند (گزارش به مالک؛ کیت تغییر نشد). (۳) `matrix`-only کیت `ids` را از `evidence/contract-rbac-findings.json` می‌خواند؛ در اجرای `all` درست شد.
- **توقف‌ها:** `BLOCKED` (گیت قرمز بعد از ۳ تلاش) | سؤال بسته برای مالک: گیت کیت سه‌ارزشی بفهمد (تغییر کیت، نیاز تأیید) یا WP 0.2 با گیت سه‌ارزشی پذیرفته شود (AD‑10).
- **نحوهٔ برگرداندن:** `git revert` همان commit. تغییرات در AD‑10 فهرست شده.
- **ادامه:** بر اساس قانون (ریز‑حلقه: گیت قرمز رد نمی‌شود و توقف کل حلقه نیست)، حلقه به WP مستقل بعدی می‌رود (0.4 → 0.7 → فاز ۲). WP 0.2 `BLOCKED` باز می‌ماند.

## WP 0.4 · F‑07 · پوشش per-directory با آستانه‌های بریف — DONE

WP: 0.4 · F: F‑07 · شاهد: `evidence/after/wp04/` · تصمیم: AD‑11 · commit: (این کامیت؛ شاخهٔ `arena/da474b65-mp`)

- **بازیابی محیط (پیش از کار):** محیط بازنشانی شده بود: `/home/user/audit-run` و venv و `/tmp` نبودند؛ شاخهٔ محلی روی `662ff88` بود با ۱۲۹ تغییر کاری نامرتبط. این تغییرات **حذف نشدند**: patch و tar در `/home/user/recovery3/` و `git stash` (`recovery3-pre-sync-wp04`) ذخیره شد. شاخه به `origin/arena/da474b65-mp` = `b6f347f` هم‌گام شد؛ WP 0.4 فقط دو فایل از stash بازآوری شد. venv تازه: `/home/user/wp04-venv` (`pip install -e ".[dev]"` exit 0).
- **پیش‌سنجش (قبل از تغییر):** `coverage run` با `pytest-cov` روی کل بک‌اند: `1199 passed, 2 skipped`، exit 0؛ گیت per-directory ⇒ **exit 1**: `db` ۷۰٫۳۰٪ (آستانه ۸۰)، `scripts` ۴۸٫۳۲٪ (آستانه ۶۰).
- **علت `db`:** migrationها در تست‌ها در subprocess اجرا می‌شوند؛ پوشش فرزند ثبت نمی‌شد (`39f0cd2d8531` = ۵٪). تلاش in-process با `alembic` API سه بار شکست خورد (خروجی `check` در بافر دیده نشد، ۴ تست drift/round‑trip/backup قرمز) ⇒ برگردانده شد.
- **اصلاح ۱ (اندازه‌گیری):** `mp-app/backend/coverage-subprocess.rc` (`parallel = True`) + `COVERAGE_PROCESS_START` + `coverage run --parallel-mode` + `coverage combine` در `scripts/coverage_run.sh`. با همین، `db/migrations/versions/39f0cd2d8531` = ۱۰۰٪ و `db` = ۹۸٫۹۷٪.
- **اصلاح ۲ (تست‌ها برای `scripts`):** `tests/integration/test_deploy_gate_branches.py` (۲۲ تست، شاخه‌های bad/warn/crash روی درخت موقت)، `test_import_food_catalog.py` (۱۳ تست)، `test_attach_exercise_media.py` (۶ تست). `scripts` از ۵۷٫۴۲٪ (با migrations) به **۶۵٫۸۵٪** رسید.
- **گیت `scripts/coverage_gate.py` + تست:** `tests/integration/test_coverage_gate.py` (۶ تست سبز). **قرمز:** جهش‌یافتهٔ گیت (`if percent + 1e-9 < minimum:` ⇒ `if False:`) در یک کپی موقت ⇒ ۳ تست ناموفق (`test_evaluate_fails_below_threshold_and_on_missing_directory`، `test_low_directories_are_not_hidden_by_total[db]`، `[scripts]`)؛ نسخهٔ اصلی ⇒ ۶ پاس؛ گیت روی XML قبل از اصلاح ⇒ exit 1.
- **CI:** `.github/workflows/ci.yml` مرحلهٔ تست به `bash scripts/coverage_run.sh` تغییر کرد (کد خروج غیرصفر = شکست) و `actions/upload-artifact` با نام `backend-coverage-xml` (`coverage.xml` + `coverage-by-dir.json`، `if: always()`). `.gitignore`: `.coverage.*`، `coverage-by-dir.json`.
- **lint/security:** ruff (`E,F,W,I,N,UP,B,SIM,DTZ,TRY400,S`) و `ruff format --check` روی ۵ فایل جدید ⇒ exit 0؛ `ruff check` کامل ⇒ exit 0؛ `bandit -r . -ll` ⇒ exit 0، ۰ مورد (B314 در `coverage_gate.py` با `nosec` و توضیح؛ AD‑11).
- **اجرای نهایی روی وضعیت کامیت‌شده:** `cd mp-app/backend && bash scripts/coverage_run.sh -q` ⇒ **RUN_RC=0**؛ `1246 passed, 2 skipped, 2 warnings in 480.95s`.

| دایرکتوری | پوشش | خطوط | آستانه | وضعیت |
|---|---|---|---|---|
| modules | 92.33٪ | 4752/5147 | ≥90 | PASS |
| app | 96.62٪ | 801/829 | ≥92 | PASS |
| api | 93.69٪ | 104/111 | ≥90 | PASS |
| engine | 97.24٪ | 1058/1088 | ≥95 | PASS |
| security | 96.61٪ | 57/59 | ≥95 | PASS |
| db | 98.97٪ | 1737/1755 | ≥80 | PASS |
| jobs | 84.55٪ | 93/110 | ≥80 | PASS |
| cache | 76.60٪ | 72/94 | ≥75 | PASS |
| scripts | 65.85٪ | 883/1341 | ≥60 | PASS |
| devtools | 91.73٪ | 122/133 | — | گزارش‌شده، بدون آستانه |
| eval | 82.56٪ | 284/344 | — | گزارش‌شده، بدون آستانه |

- **دامنهٔ هر عدد:** فرمان `bash scripts/coverage_run.sh` از `mp-app/backend`؛ `source="."`، `omit tests/*`؛ فرایندهای فرزند (alembic) شامل؛ دایرکتوری = اولین بخش مسیر در XML.
- **نتیجه کلی:** TOTAL 90٪ (11011 خط، 1048 بدون پوشش) در کل بک‌اند.
- **انحراف/یادداشت:** آستانه‌ها کاهش نیافتند. `coverage.xml` (۴۳۶KB) در git نیست؛ در CI artifact است. `scripts/coverage_gate.py` با `noqa S314 / nosec B314` (ورودی XML محلی).
- **نحوهٔ برگرداندن:** `git revert` همان commit؛ AD‑11.

## WP 0.7 · BLOCKED-ENV · کیت مفقود پس از بازنشانی محیط

- **شاهد:** `ls /home/user/audit-run` ⇒ `No such file or directory`. `harness/semgrep-mp.yml` و `kit.zip` (sha256 مورد انتظار `9a192500…`) در دسترس نیستند؛ `/home/user/wp04-venv` (venv تازه) جایگزین venv قبلی شد.
- **وضعیت:** WP 0.7 به قاعدهٔ کیت وابسته است؛ بدون آن نمی‌توان شاهد معتبر تولید کرد. ساخت قاعدهٔ جایگزین، شاهد کیت محسوب نمی‌شود.
- **مورد نیاز از مالک:** بازگردانی کیت (`kit.zip` با sha256 مطابق) در `/home/user/audit-run/`، یا تأیید مسیر دیگر. پس از آن WP 0.7 از همین نقطه ادامه می‌یابد.
- **صف باقی‌مانده (بدون تغییر):** WP 0.2 BLOCKED (AD‑10)؛ WP 0.6 و 0.8 PARTIAL؛ فازهای ۱ (PARTIAL/BLOCKED-ENV)، ۲، ۳، ۴ هنوز انجام نشده‌اند. **ممیزی کامل نیست.**

## WP 2.5 · F‑17 · خطاهای بی‌صدا ⇒ لاگ + شمارنده — DONE

- **بررسی:** AST روی کد تولید (`app, api, modules, engine, security, db, jobs, cache`): سه `except` از F‑17 قبلاً در WP 4.5 (S110) به `debug` با traceback تبدیل شده بودند (`api/v1/monitoring.py`). باقی‌مانده: `modules/assessment/service.py:180` (`except (TypeError, ValueError): continue`).
- **قرمز (قبل از تغییر):** `tests/regression/test_wp25_silent_failures.py` ⇒ ۳ ناموفق: شمارندهٔ JP7 صفر، شمارندهٔ scrape صفر، نگهبان AST یک مورد (`service.py:180`). (یک بار خطای تست خودم — `render()` بایت برمی‌گرداند نه str — اصلاح شد؛ شکست‌های بعدی علت واقعی‌اند.)
- **سبز:** `jp7_trend` ردیف خراب را با `_log.warning` و `metrics.inc("assessment_jp7_rows_skipped")` ثبت می‌کند؛ `_log_scrape_failure` شمارندهٔ `mp_metrics_scrape_failures` را هم افزایش می‌دهد. ⇒ `4 passed`.
- **کل:** `pytest -q --no-cov` ⇒ `1250 passed, 2 skipped, exit 0` (`/home/user/wp04-cov/wp25/pytest.log`).
- **نحوهٔ برگرداندن:** `git revert` همان commit.

## WP 3.2 · F‑26 · یک شکل پاکت خطا — DONE

- **یافته:** خطاهای HTTP خود Starlette (۴۰۴ مسیر ناموجود، ۴۰۵ متد نامجاز) با `{"detail": …}` برمی‌گشتند؛ بقیهٔ API `{"error": {code, message, details}}`. کلاینت‌ها (`studio/src/lib/session.ts`، `client/lib/core/api_client.dart`) `error.message` را اول می‌خوانند و `detail` را فقط پشتیبان دارند ⇒ تغییر سازگار است.
- **قرمز:** `tests/integration/test_wp32_error_envelope.py` ⇒ `2 failed` (`{'detail': 'Not Found'}`، `{'detail': 'Method Not Allowed'}`).
- **سبز:** `app/errors.py::http_error_handler` (کد: `not_found`/`method_not_allowed`/`http_<status>`؛ پیام فارسی برای ۴۰۴ و ۴۰۵؛ هدرهای خطا مثل `Allow` حفظ می‌شوند) و ثبت در `app/main.py`. ⇒ `2 passed`.
- **کل:** `pytest -q --no-cov` ⇒ `1252 passed, 2 skipped, exit 0`.
- **یادداشت:** پیام‌های ۴۰۴/۴۰۵ متن فارسی ثابت‌اند؛ اگر مالک متن دیگری بخواهد، فقط `_HTTP_MESSAGES` تغییر می‌کند.
- **نحوهٔ برگرداندن:** `git revert` همان commit.

## وضعیت باقی‌مانده پس از WP 3.2

- WP 3.1 (F‑25): کف شناسه نیاز به نوع پارامترها دارد؛ middleware قبل از مسیریابی است. طراحی و تست جدا لازم است (احتمال شکستن کدهای رشته‌ای). باز.
- WP 0.7: BLOCKED-ENV (کیت). WP 0.2: BLOCKED (AD‑10).
- READY باقی‌مانده: 2.1، 2.2، 2.3، 2.4، 3.4، 4.3، 4.4، 4.6؛ TODO: 3.3، 3.5، 4.1، 4.2، 4.7؛ PARTIAL: 0.6، 0.8، 1.1، 1.2، 1.4.

## WP 2.5 · بازبینی پس از بازیابی کیت — DONE (`a9146c7`)

- **کیت:** `harness/semgrep-mp.yml` (semgrep 1.186.0) روی `mp-app/backend` قبل و بعد: `mp-silent-except-pass` = **۰** در هر دو (`/home/user/recovery4/semgrep-before.json`، `semgrep-after.json`؛ rc=0). نتیجهٔ دیگر: `mp-money-division` ۲ مورد (قاعدهٔ دیگر، خارج از این WP).
- **شکاف واقعی:** نام شمارنده‌ها طبق کیت نبود؛ `/health/ready` بازتاب نمی‌داد؛ `scripts/dast.py::_log_skip` فقط `debug` بود.
- **قرمز:** `test_wp25_silent_failures.py` (۲ ناموفق)، `test_wp25_dast_skip_counter.py`، `test_wp25_scrape_errors_ready.py` (KeyError `metrics_scrape_errors`) ⇒ ۴ ناموفق.
- **سبز:** `mp_assessment_jp7_rows_skipped_total`؛ `mp_metrics_scrape_errors_total` + `logger.warning` + فیلد `metrics_scrape_errors` در `/health/ready`؛ `mp_dast_errors_total{where}` در `_log_skip`. ⇒ ۶ passed.
- **lint/format:** ruff (E,F,W,I,N,UP,B,SIM,DTZ,TRY400,S) exit 0؛ `ruff format --check` exit 0.
- **کل:** `pytest -q --no-cov` (backend) ⇒ `1254 passed, 2 skipped, rc=0` (`/home/user/recovery4/wp25/pytest.log`).
- **اصلاح ثبت:** پیام commit می‌گوید «was 0 before» برای گیت semgrep؛ دقیق‌تر: گیت semgrep از قبل ۰ بود و شکاف در نام/بازتاب بود. commit منتشرشده بازنویسی نشد (بدون force-push).
- **نحوهٔ برگرداندن:** `git revert a9146c7`.

## WP 3.2 · وضعیت PARTIAL

- گیت کیت `fastapi_default_detail == 0` اندازه‌گیری نشده. probe کیت این فیلد را ندارد و کیت منجمد است؛ برای اندازه‌گیری لازم است یک نسخهٔ مخزن از probe با این یافته ساخته شود، backend زنده با seed اجرا شود و خروجی ۷۱ ⇒ ۰ ثبت شود. این کار انجام نشده.
- **تأثیر:** چهار `raise HTTPException` در `backend/devtools/sandbox_bank.py` شکل بدنه‌شان تغییر کرده است (ثبت‌شده، بررسی نشده).

## وضعیت کلی

- **ممیزی کامل نیست.** باقی‌مانده: WP 3.2 گیت زنده؛ WP 3.1 (F‑25)؛ WP 0.2 (BLOCKED، AD‑10 با کیت باید دوباره ارزیابی شود، ماتریس ۱۱۴۱ سلول)؛ WP 0.7 (کیت اکنون موجود است، باید دوباره ارزیابی شود)؛ WP 0.8؛ و صف READY/TODO.

## WP 3.2 · گیت زنده — DONE

- **probe:** نسخهٔ مخزن `probes/probe_invalid_authed.repo-copy.py` (فقط یک یافته اضافه: `fastapi_default_detail`؛ هش کیت `edd3c25c…`). کیت دست‌نخورده.
- **پایه (قبل):** `0afd240` روی `:8011` ⇒ `fastapi_default_detail = 70` (همه ۴۰۴) از ۸۷۲ سلول.
- **بعد:** `8926fcd` + اصلاح پیام ⇒ `fastapi_default_detail = 0` از ۸۷۲ سلول. وضعیت‌ها یکسان: ۴۲۲:۵۳۱، ۴۰۴:۲۲۰، ۲۰۰:۵۵، ۴۰۳:۳۴، ۴۰۰:۲۴، ۴۰۹:۸.
- **یادداشت ۷۱ در کیت:** کیت ۷۱ (۷۰×۴۰۴ + ۱×۴۰۵) نوشته؛ این probe ۴۰۵ تولید نمی‌کند. ۴۰۵ جداگانه با curl: قبل `{"detail":…}`، بعد پاکت `method_not_allowed`.
- **اصلاح حین اجرا:** `http_error_handler` پیام خاص برنامه (مثلاً `authority نامعتبر`) را با پیام عمومی جایگزین می‌کرد. red ⇒ green با `tests/regression/test_wp32_detail_preserved.py` (۱ ناموفق ⇒ ۳ سبز).
- **سازگاری کلاینت:** studio `session.ts` ابتدا `error.message` سپس `detail`؛ Flutter `api_client.dart` هر دو را می‌پذیرد.
- **کل:** `pytest -q --no-cov` ⇒ `1257 passed, 2 skipped, rc=0` (`/home/user/recovery4/wp32/pytest.log`).
- **شواهد:** `docs/MuscleParadise/audit/evidence/after/wp32/` (summary.json و لاگ‌ها). JSON کامل سلول‌ها (~۴۹۰KB) خارج از مخزن: `/tmp/run/audit-before` و `/tmp/run/audit-final`.
- **نحوهٔ برگرداندن:** `git revert` همان commit.

## WP 3.1 · F‑25 · کف شناسه — DONE

- **ریشه:** `id_guard._too_big` با `isdigit()` مقادیر منفی را نمی‌دید و `0` فقط از سقف رد نمی‌شد.
- **قرمز:** `tests/integration/test_wp31_id_floor.py` (از `app.openapi()`، چون FastAPI 0.141 مسیرها را در `_IncludedRouter` نگه می‌دارد) ⇒ ۲۴۸ از ۲۴۸ سلول ناموفق (۴۰۱ بدون `invalid_id`).
- **سبز:** `app/id_floor.py::check_path_id_floor` به‌عنوان dependency سراسری (`FastAPI(dependencies=…)`). فقط پارامترهای `*_id` (در OpenAPI همه integer) با regex `[+-]?[0-9]+\Z` سنجیده می‌شوند؛ `v < 1` یا `v > MAX_SAFE_ID` ⇒ ۴۲۲ `invalid_id`. بدون `lstrip` روی رشتهٔ اصلی. ⇒ `5 passed`.
- **گیت کیت (probe زنده، ۸۷۲ سلول):**
  - پایه (822e483): `unexpected_2xx_on_bad_id = 48`، `id_guard_rejections = 70`.
  - بعد: `unexpected_2xx_on_bad_id = 0`، `id_guard_rejections = 338` = ۴×۶۷ + ۷۰ (۶۷ = ۵۷ سلول admin + ۱۰ سلول member برای هر مقدار منفی؛ ۷۰ = مقدار سقف از middleware قبلی).
  - `server_errors_5xx = 0`، `leaked_stacktrace = 0`، `fastapi_default_detail = 0`، `tokens_live_throughout = True`.
- **بار (kit: `probe_load.py plain-dev 10 40`، اجرای پشت‌سرهم روی همان DB):** نسبت بعد/قبل — ۱۰ کارگر: rps ×۱٫۲۰، p50 ×۰٫۸۶، p95 ×۰٫۸۱؛ ۴۰ کارگر: rps ×۱٫۰۷، p50 ×۰٫۹۴، p95 ×۰٫۹۷. بدون 5xx و بدون timeout. یک اجرا برای هر مرحله؛ فقط «بدون رگرسیون» ادعا می‌شود.
- **یادداشت probe بار:** دو مسیر فهرست کیت (`/api/v1/exercises`، `/api/v1/reports/financial/summary`) در هر دو ساخت ۴۰۴ می‌دهند؛ همان‌طور که هست ثبت شد.
- **کل:** `pytest -q --no-cov` ⇒ `1262 passed, 2 skipped, rc=0` (`/home/user/recovery4/wp31/pytest.log`).
- **شواهد:** `evidence/after/wp31/` (summary.json، لاگ‌های before/after)، `evidence/after/wp31-load-ratios.json`.
- **نحوهٔ برگرداندن:** `git revert` همان commit.

## WP 0.6 · F‑24 · منسوخ‌ها و شمارش مسیرها — DONE

- **قرمز:** `tests/regression/test_wp06_deprecations_and_counts.py` — `test_no_deprecated_422_constant` ⇒ ناموفق: `app/id_floor.py:33` (خودِ WP 3.1 این ثابت را وارد کرده بود).
- **سبز:** `id_floor.py` از عدد `422` مستقیم استفاده می‌کند. دو آزمون شمارش (141 مسیر، 163 عملیات، و تطابق پیمایشگر `route_guard_gate._walk` با OpenAPI) از ابتدا سبز بودند.
- **اسکریپت‌ها:** `scripts/route_guard_gate.py` و `export_routes.py` مسیرها را با پیمایش بازگشتی می‌خوانند (چون guardها روی شیء مسیر هستند)؛ تطابق آن‌ها با OpenAPI در آزمون قفل شده است (۱۶۳ = ۱۶۳، اختلاف ۰).
- **هشدار asyncio:** `pyproject.toml` ⇒ `asyncio_default_fixture_loop_scope = "function"` (رفتار فعلی همین است).
- **بار/import:** `create_app()` و `openapi()` بدون هشدار؛ لاگ‌های `load-plain-dev` و probe بدون کلمهٔ deprecat.
- **باقی‌مانده:** هشدار httpx در `fastapi/testclient.py` (فقط تست)؛ حذفش نیازمند وابستگی `httpx2` است و تصمیم جداگانه می‌خواهد.
- **کل:** `pytest -q --no-cov` ⇒ `1265 passed, 2 skipped, rc=0` (`/home/user/recovery4/wp06/pytest.log`).
- **نحوهٔ برگرداندن:** `git revert` همان commit.

## WP 0.7 · semgrep در CI (غیرمسدودکننده) — PARTIAL

- **اجرای محلی:** `semgrep --config=.semgrep/mp-harness-rules.yml --exclude=… mp-app` ⇒ exit 0، ۵ یافته: `mp-money-division`×۲، `mp-dart-dynamic-cast`×۱، `mp-ts-float-money`×۱، `mp-ts-negative-sentinel-member-id`×۱؛ `mp-silent-except-pass`×۰ (`/home/user/recovery4/semgrep-mp-all.json`).
- **CI:** مرحلهٔ «Semgrep (harness rules, non-blocking)» در job بک‌اند با `continue-on-error: true`. YAML اعتبارسنجی شد.
- **باز:** گیت «صفر یافته» در پایان فاز ۴ و تبدیل به مسدودکننده در همان فاز.

## WP 0.8 · پین SHA — DONE (گیت کیت)

- `grep -rh "uses:" .github/workflows/` ⇒ ۴۳ خط؛ همه با SHA ۴۰‌کاراکتری؛ ۰ تگ‌محور.
- اختلاف با عدد کیت (۴۲): کیت در زمان نگارش ۴۲ دیده؛ عدد فعلی ۴۳ است و همه پین‌اند.
- `gh api repos/<repo>/commits/<sha>` برای ۷ SHA یکتا ⇒ همه یافت شد (checkout، setup-node، setup-python، upload-artifact، build-push-action، login-action، flutter-action).
- **تغییر کد:** ندارد (از قبل برقرار بود).


## WP 3.4 · پروفایل عضو لازم — DONE

- **Red:** `tests/integration/test_wp34_member_profile_required.py` با پرچم خرید روشن (`monkeypatch` روی `shop_online_purchase_enabled`، مثل `test_m59_shop.py`). پیش از اصلاح: `assert 404 == 409` (بررسی پروفایل بعد از `shop_online_closed` نبود؛ با پرچم بسته ۴۰۹ هم نمی‌رسید).
- **Fix:** `modules/shop/service.py::_own_member` ⇒ `ConflictError(..., code="member_profile_required")` (۴۰۹).
- **Green:** `test_wp34`, `test_m59_shop`, `test_phase2_shop_display` ⇒ ۵۱ passed.
- **گیت ایستا:** `scripts/deploy_gate.py::check_shop_purchase_guard` ⇒ `studio/src/pages/Shop.tsx` باید تب سبد و دکمهٔ خرید را با `purchaseOpen` شرط کند. دو تست در `test_deploy_gate_branches.py` (یکی روی مخزن واقعی، یکی قرمز با دکمهٔ بدون شرط). `deploy_gate.py` ⇒ ۱۵ بررسی، ۰ مشکل؛ `test_deploy_gate_branches` + `test_deploy_gate` ⇒ ۲۵ passed.
- **کل بک‌اند:** `pytest -q --no-cov` ⇒ `1268 passed, 2 skipped`, rc=0 (`/home/user/recovery4/wp34/pytest.log`).
- **ruff:** `check` ⇒ All checks passed؛ `format --check` ⇒ مرتب.
- **سفارش به‌نیابت:** کد آن را ندارد؛ مستندسازی‌شده در AD‑17.
- **Rollback:** `git revert <commit WP 3.4>`.

## WP 4.6 · قاعدهٔ ریال و sentinel منفی — DONE

- **Red (sentinel):** `studio/tests/nutritionNoMemberSentinel.test.tsx` ⇒ قبل از اصلاح: یک درخواست با `member_id=-1` (`expected [ Array(1) ] to deeply equal []`).
- **Fix:** `pages/Nutrition.tsx` — وقتی `memberId === null` است، fetcher `Promise.resolve(null)` برمی‌گرداند و درخواست نمی‌رود. تست سبز.
- **Float money:** `Analytics.tsx:106` (`Number(row.total_minutes)`) false positive بود؛ regex `total` هر نام حاوی آن را می‌گرفت. regex با lookahead برای `minute|visit|score|kcal` محدود شد (AD‑18). fixture `.semgrep/tests/mp-ts-float-money.ts`: ۵ ruleid و ۴ ok؛ مطابقت کامل `[3,5,7,9,11]`.
- **گیت:** `semgrep --config=.semgrep/mp-harness-rules.yml mp-app/studio/src` ⇒ exit 0، ۰ یافته (`mp-ts-float-money` و `mp-ts-negative-sentinel-member-id`).
- **استودیو:** `npx tsc --noEmit` ⇒ rc=0؛ `npx vitest run` ⇒ 46 فایل passed/1 skipped، ۲۹۹ تست passed/۹ skipped، rc=0 (`/home/user/recovery4/wp46-vitest.log`).
- **Rollback:** `git revert <commit WP 4.6>`.

## WP 2.4 · RBAC از کش تصمیم — DONE (با یک محدودیت باقی‌مانده، AD‑19)

- **Red:** `tests/regression/test_wp24_rbac_decision_cache.py` ⇒ قبل از اصلاح: `casbin ارزیابی شد 50 بار؛ باید ۱ بار`؛ `۱۰۰۰ شناسه ⇒ 1000 == 1`؛ نبود کش و نبود `mp_rbac_decisions_total`.
- **Fix:** `security/rbac.py`:
  - `_decide_raw` (بدون کش) + `_decide` (`lru_cache` با سقف ۴۰۹۶) روی مسیر نرمال‌شده؛
  - `_normalise_path`: بخش‌های عددی ⇒ `:id` (هیچ سیاستی بخش عددی تحت‌اللفظی ندارد؛ تست هم‌ارزی روی همهٔ مسیرهای OpenAPI و نمونه‌های سیاست، نقش×متد)؛
  - `get_enforcer` با قفل و ظرف تک‌خانه (بدون `global`)؛
  - `enforce` ⇒ `mp_rbac_decisions_total{role,decision}` و `mp_rbac_errors_total`.
- **Green (تست‌ها):** `test_wp24_rbac_decision_cache.py` ۶ passed؛ `test_rbac.py` + `test_routes_access_matrix.py` + `test_wp03_axis_single_guard.py` + `test_m59_shop.py` ⇒ ۹۴ passed، rc=0 (`/home/user/recovery4/wp24-rbac.log`).
- **گیت بار کیت (repro، ۸۰ نخ × ۴۰ عمق × ۴۰۰ فراخوانی = ۳۲٬۰۰۰)، اسکریپت کپی مقیاسی (تشخیصی، گیت نیست):**
  | اجرا | خطا | p50 | p95 | توان عملیاتی/s |
  |---|---|---|---|---|
  | قبل: HEAD پیش از WP 2.4 (`fe103a4`) | `SystemError` ۱ | ۱٫۰۱۶ ms | ۳۵۲ ms | ۱٬۰۰۲ |
  | بعد (۵ مسیر کیت) | ۰ | ۰٫۰۰۶ ms | ۰٫۰۱۳ ms | ۱۱۰٬۵۷۰ |
  | بعد (بار با شناسه‌های متنوع) | ۰ | ۰٫۰۰۶ ms | ۰٫۰۱۱ ms | ۱۰۹٬۱۷۵ |
  - خروجی‌ها: `evidence/after/wp24/out-*.txt`.
  - توجه: متن `note` داخل اسکریپت کیت می‌گوید «enable_cache فعال نشده»؛ این متن ایستا است و با اجرای جدید مطابقت ندارد.
- **باقی‌مانده:** کش‌miss هنوز casbin را ارزیابی می‌کند. بخش‌های غیرعددی بی‌نهایت (مثلاً `job_key` یا `run_date`) می‌توانند miss بسازند. این در AD‑19 ثبت شد.
- **Rollback:** `git revert <commit WP 2.4>`.

## CI triage روی tip `9bfc99d` (شاخهٔ `arena/5a1e37b3-mp`، بدون merge) — MEASURED-BY-YOU

- **شاخه:** کارِ قبلی روی `arena/da474b65-mp` بود (PR #23 بسته‌شده، merge نشده). شاخهٔ جاری `arena/5a1e37b3-mp` از main جدا شده بود؛ با `git merge --ff-only origin/arena/da474b65-mp` همان کامیت‌ها (بدون بازنویسی) به شاخهٔ جاری آمدند. تاریخ `9bfc99d` بی‌تغییر است.
- **job ها روی `9bfc99d`** (`gh run list`): `backend` ✗ (Test)، `live-contract` ✗ (Seed + run API)، `Documentation links and handoff` ✗ (Interaction map gate)، `secret-scan` ✗ (Scan full Git history)، `e2e-api` skipped (needs backend). `studio`، `client-flutter` و Client ✓.
- **لاگ Actions:** `gh run view --log-failed` ⇒ «failed to get run log» (302 به `release-assets`). نام تست‌ها از لاگ خوانده نشد؛ بازتولید محلی انجام شد.

### 1. backend — گیت پوشش، نه تست
- بازتولید: `bash scripts/coverage_run.sh` (`/home/user/recovery4/ci-repro/coverage.log`، RUN_RC=1).
- نتیجهٔ pytest: **1274 passed، 2 skipped، rc=0** — هیچ تستی شکست نخورد.
- شکست: `security: 94.12٪ < 95.0٪` (80/85). خطوط بی‌پوشش: `security/rbac.py` 307–309 (شاخهٔ خطای `enforce` از WP 2.4) و `security/crypto.py` 40–41 (از پیش؛ تغییر نکرده).
- **اصلاح (commit جداگانه):** `tests/regression/test_wp24_rbac_decision_cache.py::test_casbin_error_is_counted_and_reraised` — خطای casbin بالا می‌رود و `mp_rbac_errors_total` یک واحد زیاد می‌شود. این تست روی کد موجود سبز شد؛ هدفش پوشش شاخهٔ تازه است، نه رفع باگ.
- **بعد از اصلاح:** `RUN_RC=0`، **1275 passed، 2 skipped**، `security 97.65٪ (83/85)`، بقیهٔ دایرکتوری‌ها بالای آستانه (`/home/user/recovery4/ci-repro/coverage2.log`).
- آستانه کاهش نیافت.

### 2. live-contract — سرور بالا نمی‌آید (curl exit 7)
- علت سنجش‌شده: `app/main.py::_assert_explicit_environment` بدون `MP_ENVIRONMENT` صریح `RuntimeError` می‌دهد (`/tmp/ci-live/api.log`). گام CI این متغیر را ست نمی‌کند.
- سنجه: با `MP_ENVIRONMENT=development` ⇒ `/health` = 200.
- **اصلاح (commit جداگانه):** `.github/workflows/ci.yml` گام «Seed + run API» ⇒ `env: MP_ENVIRONMENT: development`. اعتبارسنجیِ سرور حذف نشد.
- **بعد از اصلاح (دقیقاً دستورهای گام):** seed ⇒ `SEED_RC=0`؛ `curl -sf /health` ⇒ `{"status":"ok"}`، `HEALTH_RC=0`؛ `npm test -- tests/liveContract.test.ts` ⇒ **9 passed، rc=0** (`/tmp/ci-live/livecontract.log`).
- معرّفی‌شده در `ccf44ce` (WP 1.1/1.2)، نه در این شاخه‌ها.

### 3. Documentation links and handoff — رانش نقشه: متوقف شد
- `python3 scripts/interaction_map.py --check` ⇒ `رانش قرارداد 0` و فقط «نقشه کهنه است».
- بازتولید برای بررسی (سپس برگردانده شد؛ commit نشده): ۱۳ خط تغییر در **نقش‌های قرارداد** و **تست‌ها**، نه فقط WP 3.4. نمونه: `/api/v1/admin/users` از `manager, admin, super_admin` به `super_admin`؛ `/api/v1/auth/sessions` و `/api/v1/auth/phone-change/*` و `/api/v1/auth/otp/request` نقش‌های جدید؛ `studio-page:Analytics` از بی‌تست خارج شد؛ تست‌های جدید.
- منبع: `mp-app/backend/api/routes.json` از `b6f347f` (WP 0.2، بازتولید guardها) و تغییرات بعدی؛ WP 3.4 (`fc402a8`) فایل `routes.json` را تغییر نداد.
- **نتیجه:** این رانش «دقیقاً تغییر WP 3.4» نیست ⇒ طبق دستور، بازتولید نقشه commit نشد. **نیازمند تصمیم شما:** آیا این تغییرات نقش (که در `routes.json` از WP 0.2 است) عمدی و قابل قبول‌اند؟

### 4. secret-scan — بلاک‌شده (BLOCKED-ENV)
- برای گرفتن گزارش gitleaks به نسخهٔ ۸٫۳۰٫۱ نیاز است. دانلود `release-assets.githubusercontent.com` از این محیط ممکن نیست (`curl` خطای SSL/تونل؛ آن میزبان در فهرست مجاز نیست). بدون گزارش، هیچ انگشت‌نگاری‌ای اضافه نشد.
- `docs/MuscleParadise/audit/evidence/detect-secrets.json` **۶۷ فایل** با `hashed_secret` دارد، نه فقط ۵ مورد. نیاز است گزارش gitleaks واقعی بررسی شود تا معلوم شود کدام یافته‌ها در کدام مسیرها هستند (شرط «هر یافتهٔ بیرون از مسیر ⇒ توقف»).
- **تعارض شماره:** `AD‑11`، `AD‑12`، `AD‑13` در `DECISIONS.md` از قبل معنای دیگری دارند (پوشش، ایمنی، پیام خطا). تصمیم‌های جدید باید شماره‌های بعدی بگیرند.
- **F‑33 (تأیید شد):** گام CI فقط `--redact` دارد (نه `--redact=100`) و فاقد `--log-opts=--all`، `--ignore-gitleaks-allow` و `--gitleaks-ignore-path` است؛ تست خود مخزن (`scripts/test_retired_signing_scan.py` خط ۹۷) همهٔ آن‌ها را دارد. اسکنرِ CI ضعیف‌تر از تستش است.

### وضعیت چهار job
| job | وضعیت |
|---|---|
| backend | ✓ محلی (`RUN_RC=0`) — نیاز به push و CI واقعی |
| live-contract | ✓ محلی (seed + health + 9/9) — نیاز به push و CI واقعی |
| Documentation links and handoff | ✗ — تصمیم مالک لازم است |
| secret-scan | ✗ — BLOCKED-ENV (نبود gitleaks) |

- بسته‌های ۲ تا ۶ شروع نشدند (طبق قاعدهٔ «تا چهار job سبز نشده‌اند»).

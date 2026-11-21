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

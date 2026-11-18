# گزارش بازبینی کد M10 — CI/CD (code-reviewer)

**بازبین:** ایجنت code-reviewer | **تاریخ:** 2026-11-14 (بازبینی پس‌انداخت — backfill)

## دامنه
`.github/workflows/ci.yml` (۴ job)، `deploy.yml` (Dokploy + health-gate + rollback)، `mp-app/infra/Dockerfile.backend`، `infra/scripts/rollback.sh`، `tests/integration/test_ci_artifacts.py`.

## یافته‌ها
- ✅ زنجیره lint→test→scan→build→e2e با jobهای مستقل؛ rollback.sh با `bash -n` معتبر
- ✅ Dockerfile: uvicorn روی 8751، لایه‌های cache-friendly
- ⚠️ workflowها در sandbox اجرا نمی‌شوند (D-002/003/004) — اعتبارسنجی با تست‌های ساختار YAML (test_ci_artifacts)

## حکم
**صفر Blocker** — ۱۰۱ تست سبز.

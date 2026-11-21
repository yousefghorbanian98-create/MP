WP 0.4 (F-07) — شاهد پوشش per-directory (کامیت همین WP).

فرمان (از mp-app/backend):   bash scripts/coverage_run.sh
  = COVERAGE_PROCESS_START=<coverage-subprocess.rc> coverage run --parallel-mode -m pytest -p no:cacheprovider -q
    coverage combine ; coverage xml -o coverage.xml ; coverage report ; python scripts/coverage_gate.py --xml coverage.xml --json coverage-by-dir.json
scope:  mp-app/backend (source ".", omit tests/*). دایرکتوری = اولین بخش مسیر.
        فرایندهای فرزند (alembic در تست‌های migration) شامل‌اند.
نتیجه:  full-run.log ⇒ 1246 passed, 2 skipped، exit 0 (RUN_RC=0)؛ coverage-by-dir.json ⇒ همهٔ آستانه‌ها PASS.
XML کامل (~436KB) در git نیست؛ در CI به‌عنوان artifact با نام backend-coverage-xml منتشر می‌شود.

#!/usr/bin/env bash
# WP 0.4 (F-07): اجرای کامل پوشش بک‌اند با اندازه‌گیری per-directory.
#
# فرمان (از mp-app/backend):
#   bash scripts/coverage_run.sh [آرگومان‌های pytest]
#
# خروجی‌ها:
#   coverage.xml              — گزارش XML (برای CI artifact و gate)
#   coverage-by-dir.json      — جدول per-directory (scripts/coverage_gate.py)
# کد خروج: کد خروج pytest یا gate، هرکدام غیرصفر باشد.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2

export COVERAGE_PROCESS_START="$PWD/coverage-subprocess.rc"
rm -f .coverage .coverage.* coverage.xml coverage-by-dir.json

python -m coverage run --parallel-mode -m pytest -p no:cacheprovider "$@"
pytest_rc=$?

python -m coverage combine -q || exit 3
python -m coverage xml -o coverage.xml || exit 3
python -m coverage report | tail -n 1
python scripts/coverage_gate.py --xml coverage.xml --json coverage-by-dir.json
gate_rc=$?

if [ "$pytest_rc" -ne 0 ]; then exit "$pytest_rc"; fi
exit "$gate_rc"

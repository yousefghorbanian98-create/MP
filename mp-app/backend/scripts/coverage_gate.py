#!/usr/bin/env python3
"""WP 0.4 / F-07 — گیت پوششِ هر دایرکتوری.

# چرا این فایل وجود دارد

گیت CI فقط یک عدد کل داشت (`--cov-fail-under=70`). یک دایرکتوری ضعیف زیر
یک میانگین خوب پنهان می‌ماند (F‑07: `db` ۷۰٫۴٪ و `scripts` ۴۶٫۲٪ در حالی که
کل پروژه بالای آستانه بود). این گیت برای هر دایرکتوریِ تعیین‌شده آستانه می‌گذارد.

# قواعد

- آستانه‌ها ثابت‌اند و از بریف WP 0.4 می‌آیند. **پایین‌آوردن آستانه ممنوع**.
- دایرکتوری بدون داده در XML ⇒ شکست (پوشش‌نشده نباید سبز شود).
- دایرکتوری‌های بی‌آستانه (مثل `eval`، فایل‌های ریشه) گزارش می‌شوند ولی گیت نمی‌کنند؛
  فهرست آن‌ها در خروجی JSON است.

# فرمان

    pytest --cov=. --cov-report=xml:coverage.xml
    python scripts/coverage_gate.py --xml coverage.xml --json coverage-by-dir.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from defusedxml import ElementTree as SafeElementTree

# آستانهٔ هر دایرکتوری (درصد خطوط). منبع: بریف WP 0.4 / F‑07.
THRESHOLDS: dict[str, float] = {
    "modules": 90.0,
    "app": 92.0,
    "api": 90.0,
    "engine": 95.0,
    "security": 95.0,
    "db": 80.0,
    "jobs": 80.0,
    "cache": 75.0,
    "scripts": 60.0,
}

ROOT_BUCKET = "(root)"


def bucket_of(filename: str) -> str:
    """نام دایرکتوری سطح‌اول؛ فایل‌های ریشه در «(root)» می‌روند."""
    parts = Path(filename).parts
    if len(parts) <= 1:
        return ROOT_BUCKET
    return parts[0]


def aggregate(xml_path: Path) -> dict[str, dict[str, int]]:
    """{دایرکتوری: {'lines': n, 'covered': m}} از خطوط هر فایل در coverage XML."""
    # Coverage XML is CI-generated, but parse defensively in case an artifact is replaced.
    tree = SafeElementTree.parse(xml_path)
    totals: dict[str, dict[str, int]] = defaultdict(lambda: {"lines": 0, "covered": 0})
    for cls in tree.iter("class"):
        filename = cls.get("filename") or ""
        if filename.startswith("tests/") or "/tests/" in filename:
            continue
        bucket = totals[bucket_of(filename)]
        for line in cls.iter("line"):
            bucket["lines"] += 1
            if int(line.get("hits", "0")) > 0:
                bucket["covered"] += 1
    return dict(totals)


def evaluate(totals: dict[str, dict[str, int]]) -> tuple[list[str], dict[str, dict]]:
    """برگرداندن (شکست‌ها، جدول). شکست = دایرکتوری زیر آستانه یا بدون داده."""
    failures: list[str] = []
    table: dict[str, dict] = {}
    for name, minimum in THRESHOLDS.items():
        data = totals.get(name)
        if not data or data["lines"] == 0:
            failures.append(f"{name}: بدون داده در coverage XML (آستانه {minimum}٪)")
            table[name] = {"lines": 0, "covered": 0, "percent": None, "threshold": minimum}
            continue
        percent = 100.0 * data["covered"] / data["lines"]
        table[name] = {
            "lines": data["lines"],
            "covered": data["covered"],
            "percent": round(percent, 2),
            "threshold": minimum,
        }
        if percent + 1e-9 < minimum:
            failures.append(f"{name}: {percent:.2f}٪ < {minimum}٪")
    for name, data in sorted(totals.items()):
        if name not in THRESHOLDS:
            table[name] = {
                "lines": data["lines"],
                "covered": data["covered"],
                "percent": round(100.0 * data["covered"] / data["lines"], 2)
                if data["lines"]
                else None,
                "threshold": None,
            }
    return failures, table


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--xml", type=Path, required=True)
    parser.add_argument("--json", type=Path, help="خروجی JSON جدول به‌ازای هر دایرکتوری")
    args = parser.parse_args(argv)

    totals = aggregate(args.xml)
    failures, table = evaluate(totals)

    for name, row in table.items():
        threshold = "—" if row["threshold"] is None else f"{row['threshold']}٪"
        percent = "—" if row["percent"] is None else f"{row['percent']:.2f}٪"
        print(f"{name:<10} {percent:>8}  {row['covered']}/{row['lines']}  آستانه {threshold}")
    if args.json:
        args.json.write_text(
            json.dumps(table, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
    if failures:
        print("\nFAIL — زیر آستانه:")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("\nPASS — همهٔ دایرکتوری‌های تعیین‌شده بالای آستانه‌اند.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

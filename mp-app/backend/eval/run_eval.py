"""اجرای CLI هارنس ارزیابی + نوشتن گزارش JSON/Markdown (شواهد پایان‌نامه).

اجرا: `python -m eval.run_eval [--out finn/reports/eval]`
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eval.harness import run_all


def _fa_num(n: float | int) -> str:
    return str(n).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def to_markdown(result: dict, title: str) -> str:
    g = result["gold_agreement"]
    zero = "✅ صفر"
    lines = [
        f"# گزارش ارزیابی موتور — {title}",
        "",
        "> تولیدشده با `python -m eval.run_eval` — معیارها: ایمنی (گیت جمعیتی + محدودیت‌ها)،",
        "> یکپارچگی کتابخانه، ساختار، قطعیت (G8)، توافق با استاندارد طلایی مربی.",
        "",
        "## خلاصهٔ معیارها",
        "",
        "| معیار | مقدار | وضعیت |",
        "|---|---|---|",
        f"| سناریوها (تولید/مسدود) | {_fa_num(result['scenarios_generated'])} / {_fa_num(result['scenarios_blocked'])} | — |",
        f"| نقض گیت جمعیتی | {_fa_num(len(result['safety_population_violations']))} | "
        + (zero if not result["safety_population_violations"] else "❌")
        + " |",
        f"| نقض محدودیت حرکتی | {_fa_num(len(result['safety_constraint_violations']))} | "
        + (zero if not result["safety_constraint_violations"] else "❌")
        + " |",
        f"| مشکل یکپارچگی کتابخانه | {_fa_num(len(result['library_integrity_problems']))} | "
        + (zero if not result["library_integrity_problems"] else "❌")
        + " |",
        f"| مشکل ساختاری | {_fa_num(len(result['structural_problems']))} | "
        + (zero if not result["structural_problems"] else "❌")
        + " |",
        f"| قطعیت (G8) | {'✅' if result['determinism_pass'] else '❌'} | — |",
        f"| توافق با استاندارد طلایی | {_fa_num(g['pct'])}٪ ({_fa_num(g['matching_slots'])} از {_fa_num(g['total_slots'])} ست) | — |",
        "",
    ]
    for key, label in (
        ("safety_population_violations", "جزئیات نقض گیت جمعیتی"),
        ("safety_constraint_violations", "جزئیات نقض محدودیت"),
        ("library_integrity_problems", "جزئیات یکپارچگی کتابخانه"),
        ("structural_problems", "جزئیات مشکلات ساختاری"),
    ):
        if result[key]:
            lines.append(f"### {label}")
            lines.append("")
            lines.extend(f"- {p}" for p in result[key])
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="finn/reports/eval")
    parser.add_argument("--title", default="ارزیابی موتور")
    parser.add_argument("--stem", default="eval-report")
    args = parser.parse_args()

    result = run_all()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.stem}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out / f"{args.stem}.md").write_text(to_markdown(result, args.title), encoding="utf-8")
    print(json.dumps(result["gold_agreement"], ensure_ascii=False))
    print(
        f"violations: population={len(result['safety_population_violations'])} "
        f"constraint={len(result['safety_constraint_violations'])} "
        f"library={len(result['library_integrity_problems'])}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""گیت بهداشت مخزن — جلوی بازگشت خاموش ابزارهای سنگین را می‌گیرد.

چرا این فایل وجود دارد: در ۲۰۲۶-۱۱-۱۹ ابزار تحلیل مخزن (Repowise) نصب و اجرا شد.
آن ابزار به‌طور پیش‌فرض سه چیز را در مخزن می‌نویسد: پوشهٔ ایندکس ۵۷ مگابایتی،
فایل‌های دستورالعمل مخصوص ویرایشگر (`.claude/`, `.github/copilot-instructions.md`)
و یک git hook برای ایندکس خودکار پس از هر commit. تجربهٔ ECC نشان داد که
دستورالعمل‌های موازی و hookهای پنهان بعداً ردیابی نمی‌شوند؛ پس این گیت سه شرط را
قفل می‌کند:

1. ایندکس ابزار gitignore شده باشد (هیچ فایل ۵۷ مگابایتی وارد Git نشود).
2. هیچ پوشهٔ `.claude/` ردیابی‌شده‌ای وجود نداشته باشد (AGENTS.md تنها منبع است).
3. هیچ git hook فعالی نام ابزار را نداشته باشد (ایندکس باید دستی اجرا شود).

گیت عمداً روی «حالت فعلی» کار می‌کند، نه روی تاریخچه.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX_DIR = ".repowise"
AGENT_TOOL_MARKERS = ("repowise", "Repowise")


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return result.stdout.strip()


def check_index_ignored(problems: list[str]) -> None:
    gitignore = ROOT / ".gitignore"
    if not gitignore.is_file():
        problems.append("‏.gitignore وجود ندارد؛ ایندکس ابزار می‌تواند وارد Git شود")
        return
    patterns = {
        line.strip().rstrip("/")
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    if INDEX_DIR not in patterns:
        problems.append(f"‏{INDEX_DIR}/ در .gitignore نیست")
    tracked = _git("ls-files", INDEX_DIR)
    if tracked:
        first = tracked.splitlines()[0]
        problems.append(f"فایل ایندکس داخل Git ردیابی می‌شود: {first}")


def check_no_agent_folder(problems: list[str]) -> None:
    tracked = _git("ls-files", ".claude")
    if tracked:
        first = tracked.splitlines()[0]
        problems.append(f"‏.claude/ در Git ردیابی می‌شود: {first}")


def check_hooks(problems: list[str]) -> None:
    hooks_dir = ROOT / ".git" / "hooks"
    if not hooks_dir.is_dir():
        return
    for hook in sorted(hooks_dir.iterdir()):
        if not hook.is_file() or hook.name.endswith(".sample"):
            continue
        try:
            text = hook.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for marker in AGENT_TOOL_MARKERS:
            if marker in text:
                problems.append(f"git hook فعال نام ابزار را دارد: .git/hooks/{hook.name}")
                break


def main() -> int:
    problems: list[str] = []
    check_index_ignored(problems)
    check_no_agent_folder(problems)
    check_hooks(problems)
    if problems:
        print("Repository hygiene gate FAILED:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print(
        "Repository hygiene gate passed: index ignored, no tracked .claude/, "
        "no agent-tool git hook."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

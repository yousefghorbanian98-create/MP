#!/usr/bin/env python3
"""گیت «digestهای crosswalk با HEAD می‌خوانند» — MEM-03 fix.

# چرا این گیت لازم است

`evidence/**/*-crosswalk.json` ادعا می‌کند «این بررسی روی این منبع انجام شد» و
هر منبع را با SHA-256 ثبت می‌کند. آن ادعا فقط تا وقتی معتبر است که digest با
فایل واقعی همان checkout برابر باشد. در ۲۰۲۶-۱۱-۲۷ مشخص شد `api.ts` پس از
تولید artifact عوض شده بود و کسی متوجه نشد، چون هیچ گیتی این invariant را
نمی‌سنجید؛ `crosswalk_v2.py` فقط `tracked_dirty` را **می‌نوشت**.

# چه چیزی بررسی می‌شود

1. هر `evidence/**/*-crosswalk.json`. فایل‌های `*.STALE.json` از **داوری** خارج‌اند
   (نامشان می‌گوید ادعای جاری نیستند) ولی از **بازرسی** نه: `tracked_dirty=true`
   در آن‌ها خطاست (نقض همان قاعده) و کهنگی‌شان با خط `STALE <path> recorded=…
   actual=…` گزارش می‌شود تا پنهان نماند.
2. `meta.tracked_dirty` باید `false` باشد؛ digest روی درخت dirty بازتولیدپذیر نیست.
3. هر جفت (`path`, digest) در `meta.sources` باید با SHA-256 فایل واقعی
   `mp-app/<path>` برابر باشد. سه شکل پذیرفته می‌شود: `sha256_b64:<base64url>`
   (قالب جاری؛ دیگر ۶۴-hex نیست تا قاعدهٔ `generic-api-key` را فعال نکند)،
   `sha256:<hex>` و `<hex>` (artifactهای تاریخی).
4. اگر `meta.sha` در این checkout قابل‌حل باشد، هیچ‌کدام از فایل‌های `sources`
   نباید از آن commit تا HEAD تغییر کرده باشد. در cloneهای کم‌عمق (CI با
   `fetch-depth: 1`) این بررسی با یادداشت رد می‌شود، چون commit در دسترس نیست —
   نه اینکه pass شود.

خروجی: در هر خطا `<artifact>: ...`، و exit 1. هیچ محتوای فایل یا مقدار حساسی
چاپ نمی‌شود؛ فقط digestهای کوتاه‌شده.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
SOURCE_ROOT = ROOT / "mp-app"


def sh(*args: str) -> str | None:
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode:
        return None
    return result.stdout.strip()


def actual_digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def shorten(digest: str | None) -> str:
    if not digest:
        return "missing"
    return digest[:12]


def recorded_hex(value: object) -> str | None:
    """digest ثبت‌شده → hex خالص؛ فرم ناشناخته → None.

    سه شکل پذیرفته می‌شود: `sha256_b64:<43/44 base64url>`، `sha256:<hex>` و `<hex>`.
    """
    if not isinstance(value, str) or not value:
        return None
    if value.startswith("sha256_b64:"):
        encoded = value.split(":", 1)[1]
        padding = "=" * (-len(encoded) % 4)
        try:
            raw = base64.urlsafe_b64decode(encoded + padding)
        except (ValueError, TypeError):
            return None
        if len(raw) != 32:
            return None
        return raw.hex()
    candidate = value.split(":", 1)[1] if value.startswith("sha256:") else value
    if len(candidate) != 64 or any(ch not in "0123456789abcdef" for ch in candidate.lower()):
        return None
    return candidate.lower()


def is_stale(path: Path) -> bool:
    return path.name.endswith(".STALE.json")


def all_crosswalks() -> list[Path]:
    """هر دو نام‌گذاری: `x-crosswalk.json` و `x-crosswalk.STALE.json`.

    نکتهٔ واقعی: `rglob("*-crosswalk.json")` فایل `*-crosswalk.STALE.json` را
    **نمی‌گیرد**؛ نسخهٔ اول همین گیت همین‌جا کور بود. پس الگو صریح است.
    """
    if not EVIDENCE.is_dir():
        return []
    return sorted(
        path
        for path in EVIDENCE.rglob("*.json")
        if path.name.endswith("-crosswalk.json") or path.name.endswith("-crosswalk.STALE.json")
    )


def artifacts() -> list[Path]:
    return [path for path in all_crosswalks() if not is_stale(path)]


def stale_artifacts() -> list[Path]:
    return [path for path in all_crosswalks() if is_stale(path)]


def inspect_stale(path: Path) -> tuple[list[str], list[str], bool]:
    """artifact کهنه: dirty خطاست، کهنگی گزارش می‌شود (نه fail).

    منطق: «STALE» یعنی «این ادعا جاری نیست»، نه «این فایل بدون بازرسی رها شود».
    کسی که فردا `git mv x.json x.STALE.json` می‌کند نباید بتواند از گیت فرار کند.
    """
    problems: list[str] = []
    report: list[str] = []
    artifact = path.relative_to(ROOT).as_posix()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{artifact}: JSON خوانده نشد ({type(exc).__name__})"], report, False
    meta = payload.get("meta") if isinstance(payload, dict) else None
    if not isinstance(meta, dict):
        return [f"{artifact}: meta ندارد"], report, False

    dirty = meta.get("tracked_dirty", meta.get("dirty"))
    dirty_flag = dirty is True
    if dirty is True:
        problems.append(
            f"{artifact}: artifact کهنه هم نباید روی درخت dirty ساخته شده باشد "
            f"(tracked_dirty={dirty!r})"
        )

    sources = meta.get("sources")
    if not isinstance(sources, dict) or not sources:
        problems.append(f"{artifact}: meta.sources ندارد")
        return problems, report, dirty_flag

    for relative, recorded in sorted(sources.items()):
        actual = actual_digest(SOURCE_ROOT / relative)
        expected = recorded_hex(recorded)
        # P0 — همان دو بررسی `check()`، وگرنه یک حالت کور می‌ماند: اگر هم digest
        # ثبت‌شده خراب باشد و هم فایل در checkout نباشد، `None == None` می‌شود و
        # artifact «سالم» گزارش می‌شد. هر کسی می‌توانست با `git rm` یک منبع، گیت را
        # بی‌صدا کند. STALE یعنی «داوری نمی‌شود»، نه «بازرسی نمی‌شود».
        if expected is None:
            problems.append(f"{artifact}: {relative} digest نامعتبر ({recorded!r})")
        if actual is None:
            problems.append(f"{artifact}: {relative} در checkout نیست")
        report.append(
            f"STALE {artifact}: {relative} recorded={shorten(expected)} "
            f"actual={shorten(actual)}"
            f"{'' if expected is not None and actual == expected else '  ← کهنه'}"
        )
    return problems, report, dirty_flag


def sources_changed_since(sha: str, sources: list[str]) -> list[str] | None:
    """نام فایل‌های changed، یا None وقتی commit در checkout نیست (clone کم‌عمق)."""
    resolved = sh("git", "rev-parse", "--verify", f"{sha}^{{commit}}")
    if not resolved:
        return None
    paths = [f"mp-app/{path}" for path in sources]
    changed = sh("git", "diff", "--name-only", sha, "HEAD", "--", *paths)
    if changed is None:
        return None
    return [line for line in changed.splitlines() if line.strip()]


def check(path: Path) -> list[str]:
    problems: list[str] = []
    artifact = path.relative_to(ROOT).as_posix()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{artifact}: JSON خوانده نشد ({type(exc).__name__})"]
    meta = payload.get("meta") if isinstance(payload, dict) else None
    if not isinstance(meta, dict):
        return [f"{artifact}: meta ندارد"]

    if meta.get("tracked_dirty") is not False:
        problems.append(
            f"{artifact}: digest روی درخت dirty است یا tracked_dirty ثبت نشده "
            f"(tracked_dirty={meta.get('tracked_dirty')!r})"
        )

    sources = meta.get("sources")
    if not isinstance(sources, dict) or not sources:
        return problems + [f"{artifact}: meta.sources ندارد"]

    for relative, recorded in sorted(sources.items()):
        actual = actual_digest(SOURCE_ROOT / relative)
        expected = recorded_hex(recorded)
        if expected is None:
            problems.append(f"{artifact}: {relative} digest نامعتبر ({recorded!r})")
            continue
        if actual is None:
            problems.append(f"{artifact}: {relative} در checkout نیست")
            continue
        if actual != expected:
            problems.append(
                f"{artifact}: {relative} recorded={expected[:12]} actual={actual[:12]}"
            )

    sha = meta.get("sha")
    if isinstance(sha, str) and len(sha) == 40:
        changed = sources_changed_since(sha, sorted(sources))
        if changed:
            problems.append(
                f"{artifact}: منابع از {sha[:12]} تا HEAD تغییر کرده‌اند: {', '.join(changed)}"
            )
        elif changed is None:
            print(
                f"NOTE {artifact}: commit {sha[:12]} در این checkout نیست "
                "(clone کم‌عمق)؛ بررسی «منابع از آن زمان تغییر نکرده» اجرا نشد."
            )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description="digestهای crosswalk را با checkout بسنج")
    ap.add_argument("--json", action="store_true", help="خروجی JSON")
    args = ap.parse_args()

    found = artifacts()
    stale = stale_artifacts()
    errors: list[str] = []
    for path in found:
        errors.extend(check(path))

    stale_report: list[str] = []
    stale_dirty = 0
    for path in stale:
        problems, report, dirty_flag = inspect_stale(path)
        errors.extend(problems)
        stale_report.extend(report)
        stale_dirty += 1 if dirty_flag else 0
    summary = (
        f"{len(found) + len(stale)} artifact بررسی شد، "
        f"{len(stale)} STALE (گزارش‌شده)"
        + (f"، {stale_dirty} با tracked_dirty=true" if stale_dirty else "")
    )

    if args.json:
        print(
            json.dumps(
                {
                    "artifacts": [path.relative_to(ROOT).as_posix() for path in found],
                    "stale": [path.relative_to(ROOT).as_posix() for path in stale],
                    "summary": summary,
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for path in found:
            print(f"CHECK {path.relative_to(ROOT).as_posix()}")
        for path in stale:
            print(f"CHECK {path.relative_to(ROOT).as_posix()} (STALE — فقط گزارش، داوری نمی‌شود)")
        for line in stale_report:
            print(line)
        for error in errors:
            print(f"ERROR {error}", file=sys.stderr)
        if errors:
            print(
                f"Crosswalk digest gate FAILED: {len(errors)} مشکل در {len(found)} artifact. "
                "artifact را روی درخت تمیز بازتولید کن یا در نامش STALE بگذار.",
                file=sys.stderr,
            )
        else:
            print(
                f"Crosswalk digest gate passed: {len(found)} artifact، "
                "همهٔ digestها با checkout برابر و tracked_dirty=false."
            )
        print(summary)
    write_step_summary(summary, stale_report, errors)
    return 1 if errors else 0


def write_step_summary(summary: str, stale_report: list[str], errors: list[str]) -> None:
    """خلاصهٔ خواندنی در `$GITHUB_STEP_SUMMARY` — تا بدون لاگ هم دیده شود."""
    import os

    target = os.environ.get("GITHUB_STEP_SUMMARY")
    if not target:
        return
    lines = ["", "### Crosswalk digest gate", "", summary, ""]
    if stale_report:
        lines.extend(["<details><summary>STALE artifacts (گزارش، نه خطا)</summary>", ""])
        lines.extend(f"- `{line}`" for line in stale_report)
        lines.extend(["</details>", ""])
    for error in errors:
        lines.append(f"- ❌ {error}")
    try:
        with open(target, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError:
        pass


if __name__ == "__main__":
    raise SystemExit(main())

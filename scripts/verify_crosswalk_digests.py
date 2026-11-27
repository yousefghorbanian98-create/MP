#!/usr/bin/env python3
"""گیت «digestهای crosswalk با HEAD می‌خوانند» — MEM-03 fix.

# چرا این گیت لازم است

`evidence/**/*-crosswalk.json` ادعا می‌کند «این بررسی روی این منبع انجام شد» و
هر منبع را با SHA-256 ثبت می‌کند. آن ادعا فقط تا وقتی معتبر است که digest با
فایل واقعی همان checkout برابر باشد. در ۲۰۲۶-۱۱-۲۷ مشخص شد `api.ts` پس از
تولید artifact عوض شده بود و کسی متوجه نشد، چون هیچ گیتی این invariant را
نمی‌سنجید؛ `crosswalk_v2.py` فقط `tracked_dirty` را **می‌نوشت**.

# چه چیزی بررسی می‌شود

1. هر `evidence/**/*-crosswalk.json` (فایل‌های `*.STALE.json` عمداً مستثنا هستند:
   نامشان می‌گوید ادعای جاری نیستند).
2. `meta.tracked_dirty` باید `false` باشد؛ digest روی درخت dirty بازتولیدپذیر نیست.
3. هر جفت (`path`, `sha256`) در `meta.sources` باید با SHA-256 فایل واقعی
   `mp-app/<path>` برابر باشد. پیشوند `sha256:` پذیرفته می‌شود (قالب تازه) و
   فرم خالی hex هم (artifactهای قدیمی).
4. اگر `meta.sha` در این checkout قابل‌حل باشد، هیچ‌کدام از فایل‌های `sources`
   نباید از آن commit تا HEAD تغییر کرده باشد. در cloneهای کم‌عمق (CI با
   `fetch-depth: 1`) این بررسی با یادداشت رد می‌شود، چون commit در دسترس نیست —
   نه اینکه pass شود.

خروجی: در هر خطا `<artifact>: ...`، و exit 1. هیچ محتوای فایل یا مقدار حساسی
چاپ نمی‌شود؛ فقط digestهای کوتاه‌شده.
"""

from __future__ import annotations

import argparse
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
    """`sha256:<hex>` یا `<hex>` قدیمی → hex خالی؛ چیز دیگر → None."""
    if not isinstance(value, str) or not value:
        return None
    candidate = value.split(":", 1)[1] if value.startswith("sha256:") else value
    if len(candidate) != 64 or any(ch not in "0123456789abcdef" for ch in candidate.lower()):
        return None
    return candidate.lower()


def artifacts() -> list[Path]:
    if not EVIDENCE.is_dir():
        return []
    return sorted(
        path
        for path in EVIDENCE.rglob("*-crosswalk.json")
        if not path.name.endswith(".STALE.json")
    )


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
    errors: list[str] = []
    for path in found:
        errors.extend(check(path))

    if args.json:
        print(
            json.dumps(
                {
                    "artifacts": [path.relative_to(ROOT).as_posix() for path in found],
                    "errors": errors,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for path in found:
            print(f"CHECK {path.relative_to(ROOT).as_posix()}")
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
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

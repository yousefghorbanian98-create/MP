"""Build/check the single-file Persian project guide from its maintained chapters."""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
GUIDE_DIR = Path("docs/MuscleParadise/project-guide")
OUTPUT = Path("docs/MuscleParadise/PROJECT_GUIDE.fa.md")
CHAPTERS = (
    ("01-project-map.md", "chapter-01-project-map", "نقشهٔ پروژه و معماری"),
    ("02-backend-and-data.md", "chapter-02-backend-data", "Backend، API و داده"),
    (
        "03-clients-and-workflows.md",
        "chapter-03-clients-workflows",
        "کلاینت‌ها، PWA و سفرهای کاربر",
    ),
    (
        "04-development-testing-operations.md",
        "chapter-04-development-operations",
        "توسعه، آزمون، CI و عملیات",
    ),
    (
        "05-security-status-glossary.md",
        "chapter-05-security-status",
        "امنیت، وضعیت اثبات‌ها و واژه‌نامه",
    ),
)
CHAPTER_ANCHORS = {
    (GUIDE_DIR / filename).as_posix(): anchor for filename, anchor, _ in CHAPTERS
}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
HEADING = re.compile(r"^( {0,3})(#{1,6})(\s+.*|$)")
MARKDOWN_LINK = re.compile(r"(!?\[[^\]]*\]\()([^)]*)(\))")
LINK_TOKEN = re.compile(r"^(<[^>]+>|\S+)(.*)$")

HEADER = """# راهنمای جامع Muscle Paradise

> **کاربرد:** یک سند یکپارچهٔ فارسی برای شناخت محصول و پیاده‌سازی همین مخزن؛ از نقش‌ها و معماری تا routeها، مدل داده، کلاینت‌ها، توسعه، CI، عملیات، امنیت و کارهای باز.
>
> **حد شواهد:** متن از پنج فصل ماژولار زیر ساخته می‌شود و snapshot working tree زمان تولید است؛ لزوماً معادل HEAD یا build منتشرشده نیست. هرجا تصمیم مالک، کد، آزمون تاریخی، آزمون اجراشده یا هدف آینده متفاوت‌اند، آن‌ها را جدا بخوانید؛ وجود route، صفحه، فایل deployment یا تست به‌تنهایی آمادگی end-to-end یا production را ثابت نمی‌کند. برای ادعای runtime، کد/تست همان checkout، تغییرات محلی و SHA دقیق را با هم بررسی کنید.
>
> فایل پایگاه‌دادهٔ ریشه و رسیدهای خصوصی برای تهیهٔ این راهنما بازبینی نشده‌اند؛ راز، credential یا دادهٔ شخصی در آن نقل نشده است. این سند مجوز اجرای migration، backup/restore، deploy یا release نیست.

## فهرست

1. [نقشهٔ پروژه و معماری](#chapter-01-project-map)
2. [Backend، API و داده](#chapter-02-backend-data)
3. [کلاینت‌ها، PWA و سفرهای کاربر](#chapter-03-clients-workflows)
4. [توسعه، آزمون، CI و عملیات](#chapter-04-development-operations)
5. [امنیت، وضعیت اثبات‌ها و واژه‌نامه](#chapter-05-security-status)

برای فهرست ارجاعات، یادداشت snapshot و نسخهٔ فصل‌به‌فصل نیز [راهنمای ماژولار](project-guide/README.md) را ببینید.

---
"""


def rewrite_target(raw_target: str, source_path: Path) -> str:
    """Resolve a chapter-relative Markdown destination from the assembled guide."""
    match = LINK_TOKEN.match(raw_target.strip())
    if not match:
        return raw_target
    token, suffix = match.groups()
    angled = token.startswith("<") and token.endswith(">")
    target = token[1:-1] if angled else token
    parts = urlsplit(target)
    if parts.scheme or target.startswith("//") or not parts.path:
        return raw_target

    source_dir = source_path.parent.as_posix()
    resolved = posixpath.normpath(posixpath.join(source_dir, unquote(parts.path)))
    if resolved in CHAPTER_ANCHORS:
        new_path = ""
        fragment = parts.fragment or CHAPTER_ANCHORS[resolved]
    elif resolved == (GUIDE_DIR / "README.md").as_posix():
        new_path = "project-guide/README.md"
        fragment = parts.fragment
    else:
        new_path = posixpath.relpath(resolved, OUTPUT.parent.as_posix())
        if parts.path.endswith("/") and not new_path.endswith("/"):
            new_path += "/"
        fragment = parts.fragment

    new_target = urlunsplit(
        ("", "", quote(new_path, safe="/-._~:"), parts.query, fragment)
    )
    if angled:
        new_target = f"<{new_target}>"
    return new_target + suffix


def transform_chapter(source_path: Path, text: str) -> str:
    """Shift heading levels and rewrite links without touching fenced examples."""
    output: list[str] = []
    open_fence: tuple[str, int] | None = None

    for line in text.splitlines():
        fence_match = FENCE.match(line)
        if fence_match:
            marker, info = fence_match.groups()
            if open_fence is None:
                open_fence = (marker[0], len(marker))
            elif (
                marker[0] == open_fence[0]
                and len(marker) >= open_fence[1]
                and not info.strip()
            ):
                open_fence = None
            output.append(line)
            continue

        if open_fence is None:
            line = MARKDOWN_LINK.sub(
                lambda match: (
                    match.group(1)
                    + rewrite_target(match.group(2), source_path)
                    + match.group(3)
                ),
                line,
            )
            heading = HEADING.match(line)
            if heading:
                indent, marks, remainder = heading.groups()
                line = f"{indent}#{marks}{remainder}"
        output.append(line)

    return "\n".join(output).rstrip() + "\n"


def render() -> str:
    sections = [HEADER.rstrip()]
    for filename, anchor, _title in CHAPTERS:
        source_path = GUIDE_DIR / filename
        source = ROOT / source_path
        if not source.is_file():
            raise FileNotFoundError(
                f"required project-guide chapter is missing: {source_path}"
            )
        sections.extend(
            [
                f'<a id="{anchor}"></a>',
                transform_chapter(
                    source_path, source.read_text(encoding="utf-8")
                ).strip(),
            ]
        )
    return "\n\n".join(sections).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the consolidated guide is missing or stale; do not write files",
    )
    args = parser.parse_args(argv)

    try:
        expected = render()
    except OSError as exc:
        print(f"project guide assembly failed: {exc}", file=sys.stderr)
        return 1

    destination = ROOT / OUTPUT
    if args.check:
        if (
            not destination.is_file()
            or destination.read_text(encoding="utf-8") != expected
        ):
            print(
                f"{OUTPUT.as_posix()} is missing or stale; run python3 scripts/assemble_project_guide.py",
                file=sys.stderr,
            )
            return 1
        print(f"Project guide is current: {OUTPUT.as_posix()}.")
        return 0

    destination.write_text(expected, encoding="utf-8")
    print(f"Assembled {OUTPUT.as_posix()} from {len(CHAPTERS)} maintained chapters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

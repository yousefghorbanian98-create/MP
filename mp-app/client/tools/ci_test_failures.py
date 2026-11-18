#!/usr/bin/env python3
"""Emit safe GitHub annotations for failed Dart test names and source locations.

The Dart test JSON protocol can include assertion values and arbitrary printed
messages. This helper intentionally reports only test names, suite paths, and
source lines; it never forwards error text or stack traces into CI annotations.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def _escape_data(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _repo_path(raw_path: Any, workspace: Path) -> str | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = workspace / "mp-app" / "client" / path
    try:
        return path.resolve().relative_to(workspace).as_posix()
    except ValueError:
        return path.name


def _annotation(message: str) -> None:
    print(f"::error title=Flutter test failures::{_escape_data(message)}")


def main() -> int:
    if len(sys.argv) != 2:
        _annotation("Flutter test diagnostics were not given a JSON report path.")
        return 0

    report = Path(sys.argv[1])
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd())).resolve()
    suites: dict[Any, dict[str, Any]] = {}
    tests: dict[Any, dict[str, Any]] = {}
    failures: list[tuple[str | None, int | None, str]] = []
    passed = 0
    skipped = 0

    try:
        lines = report.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        _annotation("Flutter tests failed; the machine-readable test report is missing.")
        return 0

    for raw_line in lines:
        try:
            event = json.loads(raw_line)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(event, dict):
            continue

        event_type = event.get("type")
        if event_type == "suite":
            suite = event.get("suite")
            if isinstance(suite, dict):
                suites[suite.get("id")] = suite
        elif event_type == "testStart":
            test = event.get("test")
            if isinstance(test, dict):
                tests[test.get("id")] = test
        elif event_type == "testDone":
            result = event.get("result")
            if event.get("skipped") or result == "skipped":
                skipped += 1
                continue
            if result == "success":
                passed += 1
                continue

            test = tests.get(event.get("testID"), {})
            suite = suites.get(test.get("suiteID"), {})
            path = _repo_path(suite.get("path"), workspace)
            raw_line_number = test.get("root_line") or test.get("line")
            line_number = raw_line_number if isinstance(raw_line_number, int) else None
            name = test.get("name")
            if not isinstance(name, str) or not name:
                name = "unnamed test"
            failures.append((path, line_number, name))

    if not failures:
        _annotation(
            "Flutter tests exited non-zero, but the JSON report contained no failed test events."
        )
        return 0

    details = [f"Flutter tests: {passed} passed, {len(failures)} failed, {skipped} skipped."]
    details.append("Failed tests (source locations; assertion values omitted):")
    for path, line_number, name in failures[:40]:
        location = path or "<unknown source>"
        if line_number:
            location += f":{line_number}"
        details.append(f"- {location} — {name}")
    if len(failures) > 40:
        details.append(f"- {len(failures) - 40} additional failures omitted.")
    _annotation("\n".join(details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

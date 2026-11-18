#!/usr/bin/env python3
"""Emit safe GitHub annotations for failed Dart test names and source locations.

The Dart test JSON protocol can include assertion values and arbitrary printed
messages. This helper intentionally reports only test names, suite paths, and
source line numbers; it never forwards error text or stack traces into CI.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# A stack trace may use a file URI or package:mp_client URI. Match only a Dart
# source path and line number; no stack-frame text is ever copied to output.
_FILE_LOCATION = re.compile(
    r"(?<![A-Za-z0-9_])(?P<path>(?:mp-app/client/)?(?:test|lib)/[^:\s()]+\.dart):(?P<line>\d+)(?::\d+)?"
)
_PACKAGE_LOCATION = re.compile(
    r"package:mp_client/(?P<path>[^:\s()]+\.dart):(?P<line>\d+)(?::\d+)?"
)


def _escape_data(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _repo_path(raw_path: Any, workspace: Path) -> str | None:
    if not isinstance(raw_path, str) or not raw_path:
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        if path.parts[:2] == ("mp-app", "client"):
            path = workspace / path
        else:
            path = workspace / "mp-app" / "client" / path
    try:
        return path.resolve().relative_to(workspace).as_posix()
    except ValueError:
        return path.name


def _failure_location(stack_trace: Any, workspace: Path) -> tuple[str, int] | None:
    if not isinstance(stack_trace, str):
        return None
    for pattern in (_FILE_LOCATION, _PACKAGE_LOCATION):
        for match in pattern.finditer(stack_trace):
            raw_path = match.group("path")
            if pattern is _PACKAGE_LOCATION and not raw_path.startswith(("test/", "lib/")):
                raw_path = f"lib/{raw_path}"
            path = _repo_path(raw_path, workspace)
            if path and path.startswith("mp-app/client/"):
                return path, int(match.group("line"))
    return None


def _text_report_failure_locations(
    text_report: Path, workspace: Path
) -> list[tuple[str, tuple[str, int]]]:
    """Read only test-title/source-line pairs from Flutter's default reporter log."""
    try:
        lines = text_report.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    failures: list[tuple[str, tuple[str, int]]] = []
    title: str | None = None
    group_lines: list[str] = []

    def finish_group() -> None:
        if title is None or "❌" not in title:
            return
        location = _failure_location("\n".join(group_lines), workspace)
        if location is not None:
            failures.append((title, location))

    for line in lines:
        if line.startswith("::group::"):
            finish_group()
            title = line.removeprefix("::group::")
            group_lines = []
        elif line == "::endgroup::":
            finish_group()
            title = None
            group_lines = []
        elif title is not None:
            group_lines.append(line)
    finish_group()
    return failures


def _text_report_location(
    name: str,
    path: str | None,
    groups: list[tuple[str, tuple[str, int]]],
) -> tuple[str, int] | None:
    matching = [(title, location) for title, location in groups if name in title]
    if path and matching:
        basename = Path(path).name
        for title, location in matching:
            if basename in title:
                return location
    return matching[0][1] if matching else None


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
    failure_locations: dict[Any, tuple[str, int]] = {}
    failures: list[tuple[Any, str | None, int | None, str]] = []
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
        elif event_type == "error":
            test_id = event.get("testID")
            stack_trace = event.get("stackTrace", event.get("stack_trace"))
            location = _failure_location(stack_trace, workspace)
            if test_id is not None and location is not None:
                failure_locations.setdefault(test_id, location)
        elif event_type == "testDone":
            result = event.get("result")
            if event.get("skipped") or result == "skipped":
                skipped += 1
                continue
            if result == "success":
                passed += 1
                continue

            test_id = event.get("testID")
            test = tests.get(test_id, {})
            suite = suites.get(test.get("suiteID"), {})
            path = _repo_path(suite.get("path"), workspace)
            raw_line_number = test.get("root_line") or test.get("line")
            line_number = raw_line_number if isinstance(raw_line_number, int) else None
            name = test.get("name")
            if not isinstance(name, str) or not name:
                name = "unnamed test"
            failures.append((test_id, path, line_number, name))

    if not failures:
        _annotation(
            "Flutter tests exited non-zero, but the JSON report contained no failed test events."
        )
        return 0

    text_report_locations = _text_report_failure_locations(report.with_suffix(".txt"), workspace)
    details = [f"Flutter tests: {passed} passed, {len(failures)} failed, {skipped} skipped."]
    details.append("Failed tests (test names and source lines; assertion values omitted):")
    for test_id, path, line_number, name in failures[:40]:
        location = path or "<unknown source>"
        if line_number:
            location += f":{line_number}"
        detail = f"- {location} — {name}"
        failure_location = failure_locations.get(test_id) or _text_report_location(
            name, path, text_report_locations
        )
        if failure_location:
            failure_path, failure_line = failure_location
            detail += f" (failure frame: {failure_path}:{failure_line})"
        details.append(detail)
    if len(failures) > 40:
        details.append(f"- {len(failures) - 40} additional failures omitted.")
    _annotation("\n".join(details))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

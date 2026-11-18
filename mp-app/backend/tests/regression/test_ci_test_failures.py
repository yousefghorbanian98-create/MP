"""M99 — گزارش‌گر شکست تست‌های کلاینت: شمارش قابل‌اتکا، و بدون نشت مقدار.

چرا این تست هست: در چند run واقعیِ `client-flutter` فقط «جاب قرمز/سبز» دیده
می‌شد. دو مشکل از همان‌جا زاده شد:

  ۱) یک تستِ **skip‌شده** با تستِ **سبز** یکی به‌نظر می‌رسید؛ برای گیتِ haptics
     (M98) که عمداً skip می‌کند وقتی پلتفرم پیامی نمی‌فرستد، این یعنی گیت می‌تواند
     بی‌صدا توخالی شود. پس حالت ``--summary`` اضافه شد.
  ۲) برعکسش هم خطر دارد: reporter باید نام تست و مسیر/خط را بگوید ولی **هیچ**
     بخشی از متن خطا/استک‌تریس را منتشر نکند (مخزن عمومی است؛ پیام‌های تست می‌تواند
     دادهٔ واقعی داشته باشد). تست پایین همان را با یک sentinel می‌سنجد.

گیت باید روی ورودی «بد» هم قرمز/صحیح رفتار کند، وگرنه تزئینی است.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

CLIENT = Path(__file__).resolve().parents[3] / "client"
GATE = CLIENT / "tools" / "ci_test_failures.py"


def _load():
    spec = importlib.util.spec_from_file_location("ci_test_failures", GATE)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ci_test_failures"] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()

_SENTINEL = "SECRET-member-token-DO-NOT-PRINT"


def _events(*, workspace: Path, with_failure: bool, with_skip: bool = True) -> list[dict[str, Any]]:
    """حداقلِ پروتکل JSON گزارش `flutter test`: suite، testStart، testDone (و error)."""
    suite_path = workspace / "mp-app" / "client" / "test" / "motion_haptics_test.dart"
    events: list[dict[str, Any]] = [
        {
            "type": "suite",
            "suite": {"id": 0, "path": str(suite_path), "projectDirectory": str(workspace)},
        }
    ]
    results: list[tuple[int, str, str, bool]] = [
        (1, "pulse A passes", "success", False),
        (4, "pulse D passes", "success", False),
    ]
    if with_skip:
        results.append((2, "pulse B skipped on this SDK", "success", True))
    if with_failure:
        results.append((3, "pulse C fails", "failure", False))
    for test_id, name, result, skipped in results:
        events.append(
            {
                "type": "testStart",
                "test": {"id": test_id, "name": name, "suiteID": 0, "root_line": 42, "line": 42},
            }
        )
        if skipped:
            events.append(
                {"type": "testDone", "testID": test_id, "result": "success", "skipped": True}
            )
            continue
        events.append({"type": "testDone", "testID": test_id, "result": result, "skipped": False})
        if with_failure and result == "failure":
            # این دو متن عمداً حساس‌اند: reporter نباید هیچ‌کدام را رد کند.
            events.append(
                {
                    "type": "error",
                    "testID": test_id,
                    "error": f"Expected: 3\nActual: 0 — {_SENTINEL}",
                    "stackTrace": (
                        f"  test/motion_haptics_test.dart 86:7  main.<fn>\n"
                        f"  {_SENTINEL} in frame text\n"
                    ),
                }
            )
    return events


def _report(tmp_path: Path, events: list[dict[str, Any]]) -> Path:
    path = tmp_path / "flutter-test.json"
    path.write_text("\n".join(json.dumps(event) for event in events), encoding="utf-8")
    return path


@pytest.fixture(autouse=True)
def _workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    workspace = tmp_path
    (workspace / "mp-app" / "client" / "test").mkdir(parents=True)
    monkeypatch.setenv("GITHUB_WORKSPACE", str(workspace))
    return workspace


def test_summary_mode_counts_and_stays_quiet(tmp_path: Path, capsys) -> None:
    report = _report(tmp_path, _events(workspace=tmp_path, with_failure=False))
    assert gate.main(["--summary", str(report)]) == 0
    out = capsys.readouterr().out
    assert "2 passed, 0 failed, 1 skipped" in out
    # حالت خلاصه هرگز annotation قرمز نمی‌فرستد
    assert "::error" not in out


def test_summary_mode_shows_failures_without_annotation(
    tmp_path: Path, capsys, _workspace: Path
) -> None:
    report = _report(tmp_path, _events(workspace=_workspace, with_failure=True))
    assert gate.main(["--summary", str(report)]) == 0
    out = capsys.readouterr().out
    assert "2 passed, 1 failed, 1 skipped" in out
    assert "::error" not in out


def test_failure_mode_names_test_but_leaks_no_values(
    tmp_path: Path, capsys, _workspace: Path
) -> None:
    events = _events(workspace=_workspace, with_failure=True)
    report = _report(tmp_path, events)
    # فایل `.txt` هم لازم است: fallback یافتن frame از آن خوانده می‌شود و نباید
    # چیزی از متنش به خروجی برود.
    (tmp_path / "flutter-test.txt").write_text(
        "::group::motion_haptics_test.dart: pulse C fails [E]\n"
        f"  test/motion_haptics_test.dart 86:7  main.<fn> {_SENTINEL}\n"
        "::endgroup::\n",
        encoding="utf-8",
    )
    assert gate.main([str(report)]) == 0
    out = capsys.readouterr().out
    assert "Flutter test failures" in out
    assert "pulse C fails" in out
    assert "mp-app/client/test/motion_haptics_test.dart:42" in out
    assert "2 passed, 1 failed, 1 skipped" in out
    # نشتی ممنوع — حتی از متن error و stack trace
    assert _SENTINEL not in out
    assert "Expected:" not in out


def test_missing_report_is_reported_not_crashing(tmp_path: Path, capsys) -> None:
    assert gate.main([str(tmp_path / "absent.json")]) == 0
    out = capsys.readouterr().out
    assert "machine-readable test report is missing" in out


def test_summary_mode_never_blames_a_green_step(tmp_path: Path, capsys) -> None:
    # گزارش غایب در حالت خلاصه = یک خط ساده، نه ::error (خط در step موفق هم اجرا
    # می‌شود؛ «::error» در آن‌جا معادل اتهام کاذب به گیت است).
    assert gate.main(["--summary", str(tmp_path / "absent.json")]) == 0
    out = capsys.readouterr().out
    assert "summary unavailable" in out
    assert "::error" not in out

    assert gate.main(["--summary"]) == 0
    out = capsys.readouterr().out
    assert "summary unavailable" in out
    assert "::error" not in out


def test_bad_arguments_do_not_abort_the_job(capsys) -> None:
    assert gate.main([]) == 0
    assert "were not given a JSON report path" in capsys.readouterr().out

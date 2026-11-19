"""The QR formatting workflow must test the exact files before any push."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[4]
WORKFLOW = ROOT / ".github/workflows/client-format-fix.yml"


def _qr_steps():
    workflow = yaml.safe_load(WORKFLOW.read_text())
    steps = workflow["jobs"]["format-qr"]["steps"]
    return {step.get("name"): step for step in steps}, steps


def test_qr_test_is_a_required_step_before_commit_and_push():
    named, steps = _qr_steps()
    formatting = named["Resolve dependencies and format only the two QR files"]
    test = named["Run QR-only widget tests and report diagnostic"]
    commit = named["Commit formatting to the selected branch"]
    assert steps.index(formatting) < steps.index(test) < steps.index(commit)
    assert (
        "sha256sum lib/features/checkin/checkin_page.dart test/qr_biometric_gate_test.dart"
        in formatting["run"]
    )
    assert '"$RUNNER_TEMP/qr-tested-inputs.sha256"' in formatting["run"]
    assert not test.get("continue-on-error", False)
    assert not commit.get("if"), "commit must retain GitHub's default success() guard"
    assert "flutter test" in test["run"]
    assert 'exit "$status"' in test["run"]
    assert 'sha256sum --check "$RUNNER_TEMP/qr-tested-inputs.sha256"' in commit["run"]
    assert 'git hash-object --no-filters "$path"' in commit["run"]
    assert 'git rev-parse ":$path"' in commit["run"]
    assert commit["run"].index("sha256sum --check") < commit["run"].index("git add")
    assert commit["run"].index("git rev-parse") < commit["run"].index("git push")


@pytest.mark.parametrize(
    "test_exit,mutate_after_test,bad_stage",
    [(0, False, False), (3, False, False), (0, True, False), (0, False, True)],
)
def test_fake_runner_only_pushes_verified_inputs(tmp_path, test_exit, mutate_after_test, bad_stage):
    named, steps = _qr_steps()
    test_step = named["Run QR-only widget tests and report diagnostic"]
    commit_step = named["Commit formatting to the selected branch"]
    # Execute the exact workflow snippets in their documented order, with fake
    # binaries and synthetic files only. No repository or remote is touched.
    order = [test_step, commit_step]
    assert steps.index(test_step) < steps.index(commit_step)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    events = tmp_path / "events"
    flutter = bin_dir / "flutter"
    flutter.write_text(
        '#!/bin/sh\nprintf "test\\n" >> "$EVENTS"\n'
        'printf "{\\"type\\":\\"done\\"}\\n"\nexit "$FAKE_TEST_EXIT"\n'
    )
    flutter.chmod(0o755)
    git = bin_dir / "git"
    git.write_text(
        '#!/bin/sh\nprintf "git %s\\n" "$*" >> "$EVENTS"\n'
        'if [ "$1" = diff ]; then exit 1; fi\n'
        'if [ "$1" = rev-parse ] && [ "$FAKE_BAD_STAGE" = 1 ]; then echo other-hash; exit 0; fi\n'
        'if [ "$1" = hash-object ] || [ "$1" = rev-parse ]; then echo fixture-hash; fi\n'
        "exit 0\n"
    )
    git.chmod(0o755)
    client = tmp_path / "mp-app/client"
    (client / "lib/features/checkin").mkdir(parents=True)
    (client / "test").mkdir()
    (client / "lib/features/checkin/checkin_page.dart").write_text("fixture page\n")
    (client / "test/qr_biometric_gate_test.dart").write_text("fixture test\n")
    manifest = tmp_path / "qr-tested-inputs.sha256"
    with manifest.open("w") as out:
        subprocess.run(
            [
                "sha256sum",
                "lib/features/checkin/checkin_page.dart",
                "test/qr_biometric_gate_test.dart",
            ],
            cwd=client,
            stdout=out,
            check=True,
        )
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "EVENTS": str(events),
        "FAKE_TEST_EXIT": str(test_exit),
        "FAKE_BAD_STAGE": "1" if bad_stage else "0",
        "RUNNER_TEMP": str(tmp_path),
        "BRANCH": "arena/synthetic-test",
    }
    for step in order:
        cwd = tmp_path / step.get("working-directory", ".")
        result = subprocess.run(
            ["bash", "-e", "-c", step["run"]], cwd=cwd, env=env, capture_output=True
        )
        if result.returncode:
            break  # GitHub's default success() condition skips the commit step.
        if step is test_step and mutate_after_test:
            (client / "lib/features/checkin/checkin_page.dart").write_text("changed after test\n")
    lines = events.read_text().splitlines()
    assert lines[0] == "test"
    if test_exit or mutate_after_test or bad_stage:
        assert result.returncode != 0
        if test_exit:
            assert result.returncode == test_exit
        assert all(not line.startswith("git push ") for line in lines)
        if test_exit or mutate_after_test:
            assert all(not line.startswith("git ") for line in lines)
    else:
        assert result.returncode == 0, result.stderr.decode()
        assert any(line.startswith("git push ") for line in lines)

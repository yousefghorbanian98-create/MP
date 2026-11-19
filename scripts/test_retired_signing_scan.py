#!/usr/bin/env python3
"""Test exact retired signing exceptions and the real scanner using fake data.

Requires Gitleaks 8.30.1 (set GITLEAKS to its path). No project files, private
keys, or live credentials are used by the fixture. All temporary Git objects
are confined to a temporary bare repository and automatically removed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
POLICY = ROOT / ".gitleaksignore"
HISTORICAL_COMMIT = "c6f29449e8a55e0ed1204847357313ca0dd7a9cb"
SIGNING_PATH = "mp-app/client/android/keystore/keystore.properties"
EXPECTED = {
    f"{HISTORICAL_COMMIT}:{SIGNING_PATH}:generic-api-key:2",
    f"{HISTORICAL_COMMIT}:{SIGNING_PATH}:generic-api-key:4",
}


def run(args: list[str], *, env: dict[str, str], data: bytes | None = None) -> bytes:
    result = subprocess.run(args, input=data, capture_output=True, env=env, check=False)
    if result.returncode:
        # Do not expose command output: scanners and Git may handle fixture secrets.
        raise RuntimeError(f"{Path(args[0]).name} failed (exit {result.returncode})")
    return result.stdout.strip()


def main() -> None:
    lines = [line.strip() for line in POLICY.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if len(lines) != len(set(lines)):
        raise AssertionError("Duplicate ignore entry")
    fingerprint = re.compile(r"^[0-9a-f]{40}:[^:]+:[a-zA-Z0-9_-]+:[1-9][0-9]*$")
    if not all(fingerprint.fullmatch(line) for line in lines):
        raise AssertionError("Every ignore must be an exact commit/path/rule/line fingerprint")
    if {line for line in lines if HISTORICAL_COMMIT in line or SIGNING_PATH in line} != EXPECTED:
        raise AssertionError("Retired-key exceptions differ from the two reviewed findings")

    scanner = os.environ.get("GITLEAKS") or shutil.which("gitleaks")
    if not scanner:
        raise RuntimeError("Gitleaks 8.30.1 is required; set GITLEAKS to its path")
    scanner = str(Path(scanner).resolve())
    with tempfile.TemporaryDirectory(prefix="mp-gitleaks-policy-") as temp:
        tmp = Path(temp)
        home = tmp / "home"
        home.mkdir()
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(home),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Test Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "GIT_INDEX_FILE": str(tmp / "index"),
        }
        version = run([scanner, "version"], env=env).decode()
        if version.lstrip("v") != "8.30.1":
            raise RuntimeError("Expected Gitleaks 8.30.1")
        repo = tmp / "repository.git"
        run(["git", "init", "--bare", str(repo)], env=env)

        def git(*args: str, data: bytes | None = None) -> str:
            return run(["git", "-C", str(repo), *args], env=env, data=data).decode()

        def make_commit(parent: str | None) -> str:
            # Two generated fixture strings in different commits, never printed.
            body = f'placeholder=fixture\napi_key="{secrets.token_hex(32)}"\n'.encode()
            blob = git("hash-object", "-w", "--stdin", data=body)
            git("update-index", "--add", "--cacheinfo", "100644", blob, SIGNING_PATH)
            tree = git("write-tree")
            args = ["commit-tree", tree]
            if parent:
                args.extend(["-p", parent])
            return git(*args, data=b"synthetic scanner regression fixture\n")

        first = make_commit(None)
        second = make_commit(first)
        git("update-ref", "refs/fixture/scan", second)
        first_fingerprint = f"{first}:{SIGNING_PATH}:generic-api-key:2"
        second_fingerprint = f"{second}:{SIGNING_PATH}:generic-api-key:2"
        fixture_policy = tmp / "policy"
        fixture_policy.mkdir()
        ignore = fixture_policy / ".gitleaksignore"
        report = tmp / "report.json"

        def scan() -> tuple[int, set[str]]:
            result = subprocess.run(
                [scanner, "git", str(repo), "--log-opts=--all", "--redact=100", "--no-banner",
                 "--log-level=error", "--ignore-gitleaks-allow", "--gitleaks-ignore-path", str(fixture_policy),
                 "--report-format=json", "--report-path", str(report)],
                env=env, capture_output=True, check=False,
            )
            if not report.is_file():
                raise RuntimeError(f"Scanner did not write a report (exit {result.returncode})")
            findings = json.loads(report.read_text())
            return result.returncode, {entry["Fingerprint"] for entry in findings}

        ignore.write_text(POLICY.read_text())
        code, found = scan()
        if code != 1 or found != {first_fingerprint, second_fingerprint}:
            raise AssertionError("Scanner must detect both synthetic findings without fixture exception")
        ignore.write_text(POLICY.read_text() + "\n" + first_fingerprint + "\n")
        code, found = scan()
        if code != 1 or found != {second_fingerprint}:
            raise AssertionError("Exact exception must leave the new same-path/same-line finding visible")
        ignore.write_text(POLICY.read_text() + "\n" + first_fingerprint + "\n" + second_fingerprint + "\n")
        code, found = scan()
        if code != 0 or found:
            raise AssertionError("Exact fixture exceptions should suppress only those findings")
    print("PASS: reviewed exact fingerprints and synthetic Gitleaks regression (8.30.1)")


if __name__ == "__main__":
    main()

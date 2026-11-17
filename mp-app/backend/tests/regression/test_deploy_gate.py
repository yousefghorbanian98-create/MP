"""Regression coverage for the standalone deployment gate script."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]


def test_deploy_gate_accepts_checked_in_compose_and_readiness_paths() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/deploy_gate.py"],
        cwd=BACKEND,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "readiness /api/v1/health/ready" in result.stdout
    assert "Dockerfile" in result.stdout

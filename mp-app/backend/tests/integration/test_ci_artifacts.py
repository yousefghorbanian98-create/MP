"""تست‌های M10 — اعتبارسنجی artifacts CI/CD (workflowها، Dockerfile، اسکریپت rollback)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]


def test_ci_workflow_valid():
    data = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
    jobs = data["jobs"]
    for job in ["backend", "studio", "client-flutter", "e2e-api"]:
        assert job in jobs, f"job {job} در CI نیست"
    steps = [s.get("name", "") for s in jobs["backend"]["steps"]]
    assert any("Lint" in s for s in steps)
    assert any("Test" in s for s in steps)
    assert any("Security" in s for s in steps)


def test_deploy_workflow_valid():
    data = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    assert "build-and-push" in data["jobs"]
    assert "deploy" in data["jobs"]


def test_dockerfile_exists_and_exposes_port():
    df = (ROOT / "mp-app/infra/Dockerfile.backend").read_text()
    assert "EXPOSE 8751" in df
    assert "uvicorn" in df


def test_rollback_script_syntax():
    result = subprocess.run(
        ["bash", "-n", str(ROOT / "mp-app/infra/scripts/rollback.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_rollback_runbook_exists():
    rb = ROOT / "docs/MuscleParadise/runbooks/rollback.md"
    assert rb.exists()
    assert "rollback" in rb.read_text().lower()

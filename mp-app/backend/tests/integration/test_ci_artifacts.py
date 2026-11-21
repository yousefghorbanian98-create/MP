"""تست‌های M10 — اعتبارسنجی artifacts CI/CD (workflowها، Dockerfile، اسکریپت rollback)."""

from __future__ import annotations

import json
import os
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


def test_deploy_workflow_is_manual_and_pushes_sha_tagged_images():
    data = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    triggers = data.get("on", data.get(True, {}))  # PyYAML 1.1 treats `on` as a boolean key.
    assert set(triggers) == {"workflow_dispatch"}
    assert {"preflight", "build-and-push", "deploy", "rollback"} <= set(data["jobs"])
    assert (
        "github.event.repository.default_branch"
        in data["jobs"]["preflight"]["steps"][0]["env"]["DEFAULT_BRANCH"]
    )
    build = data["jobs"]["build-and-push"]
    assert build["needs"] == ["preflight"]
    assert build["permissions"]["packages"] == "write"
    # WP 0.8: ارجاع actions به SHA پین شده؛ تطبیق با نام action (نه تگ متحرک).
    push_steps = [
        step
        for step in build["steps"]
        if str(step.get("uses", "")).startswith("docker/build-push-action@")
    ]
    assert len(push_steps) == 2
    assert all(step["with"]["push"] is True for step in push_steps)
    assert all("github.sha" in step["with"]["tags"] for step in push_steps)
    assert "environment" in data["jobs"]["deploy"]
    assert data["jobs"]["deploy"]["needs"] == ["preflight", "build-and-push"]
    assert data["jobs"]["rollback"]["needs"] == ["preflight"]
    assert "workflow_dispatch" in triggers


def test_deploy_workflow_bash_steps_are_syntactically_valid():
    data = yaml.safe_load((ROOT / ".github/workflows/deploy.yml").read_text())
    for job_name, job in data["jobs"].items():
        for index, step in enumerate(job.get("steps", [])):
            script = step.get("run")
            if script:
                result = subprocess.run(
                    ["bash", "-n"], input=script, capture_output=True, text=True
                )
                assert result.returncode == 0, f"{job_name} step {index}: {result.stderr}"


def test_container_workflow_uses_sha_and_release_tags_without_latest(tmp_path):
    workflow_path = ROOT / ".github/workflows/container.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    data = yaml.safe_load(workflow_text)
    triggers = data.get("on", data.get(True, {}))
    assert set(triggers) == {"workflow_dispatch", "push"}
    assert ":latest" not in workflow_text

    job = data["jobs"]["build-push"]
    tag_step = next(step for step in job["steps"] if step.get("id") == "image-tags")
    assert "${{ steps.image-tags.outputs.backend }}" in workflow_text
    assert "${{ steps.image-tags.outputs.studio }}" in workflow_text
    syntax = subprocess.run(["bash", "-n"], input=tag_step["run"], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr

    sha = "a" * 40
    for ref_type, ref_name, release_tag in (
        ("branch", "main", None),
        ("tag", "v1.2.3", "v1.2.3"),
    ):
        output_path = tmp_path / f"{ref_type}.output"
        env = os.environ.copy()
        env.update(
            {
                "REGISTRY": "ghcr.io",
                "IMAGE_OWNER": "ExampleOwner",
                "GITHUB_SHA": sha,
                "GITHUB_REF_TYPE": ref_type,
                "GITHUB_REF_NAME": ref_name,
                "GITHUB_OUTPUT": str(output_path),
            }
        )
        result = subprocess.run(
            ["bash", "-c", tag_step["run"]], env=env, capture_output=True, text=True
        )
        assert result.returncode == 0, result.stderr
        output = output_path.read_text(encoding="utf-8")
        assert f"ghcr.io/exampleowner/mp-backend:{sha}" in output
        assert f"ghcr.io/exampleowner/mp-studio:{sha}" in output
        if release_tag:
            assert f"ghcr.io/exampleowner/mp-backend:{release_tag}" in output
            assert f"ghcr.io/exampleowner/mp-studio:{release_tag}" in output
        else:
            assert "main" not in output


def test_dockerfile_exists_and_exposes_port():
    df = (ROOT / "mp-app/infra/Dockerfile.backend").read_text()
    assert "EXPOSE 8000" in df
    assert "uvicorn" in df


def test_rollback_script_syntax():
    result = subprocess.run(
        ["bash", "-n", str(ROOT / "mp-app/infra/scripts/rollback.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_rollback_script_requires_https_and_explicit_image_without_network(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture = tmp_path / "curl-args"
    fake_curl = fake_bin / "curl"
    fake_curl.write_text(
        "\n".join(
            (
                "#!/usr/bin/env bash",
                'printf \'%s\\n\' "$@" > "$CURL_CAPTURE"',
                "printf 'mock-ok'",
                "",
            )
        ),
        encoding="utf-8",
    )
    fake_curl.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{fake_bin}{os.pathsep}{env['PATH']}"
    env["CURL_CAPTURE"] = str(capture)
    script = ROOT / "mp-app/infra/scripts/rollback.sh"
    image = f"ghcr.io/example-owner/mp-backend:{'a' * 40}"

    for webhook, invalid_image in (
        ("http://dokploy.example/webhook", image),
        ("https://dokploy.example/webhook", "ghcr.io/example-owner/mp-backend:latest"),
    ):
        result = subprocess.run(
            ["bash", str(script), webhook, invalid_image],
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode != 0
        assert not capture.exists(), "invalid input must not invoke curl"

    result = subprocess.run(
        ["bash", str(script), "https://dokploy.example/webhook", image],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    arguments = capture.read_text(encoding="utf-8").splitlines()
    payload = arguments[arguments.index("-d") + 1]
    assert json.loads(payload) == {"image": image, "action": "rollback"}


def test_rollback_runbook_exists():
    rb = ROOT / "docs/MuscleParadise/runbooks/rollback.md"
    assert rb.exists()
    assert "rollback" in rb.read_text().lower()


def test_every_github_action_is_pinned_to_commit_sha():
    """WP 0.8 / A5: هر `uses:` باید به SHA کامیت (۴۰ hex) پین باشد، نه تگ متحرک.

    ارجاع محلی (`./...`) و Docker image (`docker://`) از این قاعده مستثنا هستند.
    """
    import re

    pattern = re.compile(r"^\s*-?\s*uses:\s*(\S+)", re.MULTILINE)
    unpinned: list[str] = []
    for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
        for ref in pattern.findall(path.read_text(encoding="utf-8")):
            if ref.startswith(("./", "docker://")):
                continue
            if not re.search(r"@[0-9a-f]{40}$", ref):
                unpinned.append(f"{path.name}: {ref}")
    assert unpinned == [], "ارجاع بدون SHA: " + "; ".join(unpinned)

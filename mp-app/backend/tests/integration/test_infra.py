"""تست‌های M11 — اعتبارسنجی زیرساخت (compose، Caddyfile، Ansible، اسکریپت‌ها)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
INFRA = ROOT / "mp-app/infra"


def test_docker_compose_valid_and_complete():
    data = yaml.safe_load((INFRA / "docker-compose.yml").read_text())
    services = data["services"]
    for s in ["backend", "valkey", "ollama", "caddy"]:
        assert s in services, f"سرویس {s} در compose نیست"
    # Valkey نه Redis (لایسنس — لایهٔ ۱۲)
    assert "valkey" in services["valkey"]["image"]
    # backend در معرض اینترنت عمومی نیست (فقط caddy پورت عمومی دارد)
    assert "ports" not in services["backend"]
    assert "ports" in services["caddy"]


def test_caddyfile_security_headers():
    text = (INFRA / "Caddyfile").read_text()
    assert "X-Content-Type-Options" in text
    assert "Strict-Transport-Security" in text
    assert "reverse_proxy backend:8000" in text


def test_ansible_playbook_valid():
    data = yaml.safe_load((INFRA / "ansible/playbook.yml").read_text())
    assert isinstance(data, list) and data[0]["hosts"] == "gym_servers"
    task_names = [t.get("name", "") for t in data[0]["tasks"]]
    assert any("backup" in n.lower() for n in task_names)
    # docker و ffmpeg در پیش‌نیازها نصب می‌شوند
    apt_task = next(t for t in data[0]["tasks"] if t.get("name") == "Install prerequisites")
    assert "docker.io" in apt_task["apt"]["name"]
    assert "ffmpeg" in apt_task["apt"]["name"]


def test_compress_media_script_syntax():
    result = subprocess.run(
        ["bash", "-n", str(INFRA / "scripts/compress-media.sh")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_provisioning_runbook_exists():
    assert (ROOT / "docs/MuscleParadise/runbooks/provisioning.md").exists()

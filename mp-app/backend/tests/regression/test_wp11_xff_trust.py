"""WP 1.1 / F-01 — اعتماد به X-Forwarded-For فقط از پروکسی معتمد.

ریشهٔ نقص: uvicorn با `--forwarded-allow-ips='*'` هر peer را معتمد می‌کرد، پس
`request.client` پیش از رسیدن به اپ از هدر جعلی پر می‌شد و محدودیت نرخ OTP با
تغییر XFF دور زده می‌شد.

نکتهٔ روش‌شناسی: `TestClient` از uvicorn عبور نمی‌کند، پس نقص را بازتولید نمی‌کند.
گیت واقعی یک uvicorn زنده با همان فلگ‌های تصویر داکر است (`scripts/uvicorn_proxy_flags.sh`).
"""

from __future__ import annotations

import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest
import yaml
from pydantic import ValidationError

from app.config import Settings

from .test_production_ops import valid_production_settings

BACKEND = Path(__file__).resolve().parents[2]
MP = BACKEND.parent
DOCKERFILES = [BACKEND / "Dockerfile", MP / "infra" / "Dockerfile.backend"]
FLAGS_SCRIPT = BACKEND / "scripts" / "uvicorn_proxy_flags.sh"


def test_production_accepts_valid_trusted_proxy_list() -> None:
    settings = valid_production_settings(trusted_proxies="172.18.0.2, 10.0.0.0/8")
    assert settings.trusted_proxies == "172.18.0.2, 10.0.0.0/8"


@pytest.mark.parametrize("value", ["", "   ", "not-an-ip", "10.0.0.0/99", "1.2.3.4,bogus"])
def test_production_rejects_missing_or_invalid_trusted_proxies(value: str) -> None:
    with pytest.raises(ValidationError, match="MP_TRUSTED_PROXIES"):
        valid_production_settings(trusted_proxies=value)


def test_development_does_not_require_trusted_proxies() -> None:
    assert Settings(environment="development", trusted_proxies="").trusted_proxies == ""


@pytest.mark.parametrize("dockerfile", DOCKERFILES, ids=lambda p: p.name)
def test_dockerfile_never_trusts_wildcard_proxies(dockerfile: Path) -> None:
    text = dockerfile.read_text(encoding="utf-8")
    assert "forwarded-allow-ips='*'" not in text
    assert "forwarded-allow-ips=*" not in text
    assert "scripts/uvicorn_proxy_flags.sh" in text


def test_proxy_flags_script_is_fail_closed_without_trusted_proxies() -> None:
    env = {k: v for k, v in os.environ.items() if k != "MP_TRUSTED_PROXIES"}
    out = subprocess.run(
        ["sh", str(FLAGS_SCRIPT)], env=env, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "--no-proxy-headers"
    assert "*" not in out


def test_proxy_flags_script_trusts_only_configured_list() -> None:
    env = {**os.environ, "MP_TRUSTED_PROXIES": " 172.18.0.2 , 10.0.0.0/8 "}
    out = subprocess.run(
        ["sh", str(FLAGS_SCRIPT)], env=env, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "--proxy-headers --forwarded-allow-ips=172.18.0.2,10.0.0.0/8"


def test_compose_backend_receives_trusted_proxies() -> None:
    compose = yaml.safe_load((MP / "infra" / "docker-compose.yml").read_text(encoding="utf-8"))
    value = compose["services"]["backend"]["environment"]["MP_TRUSTED_PROXIES"]
    assert value.startswith("${MP_TRUSTED_PROXIES:?")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture()
def live_backend(tmp_path):
    """uvicorn واقعی با فلگ‌های تصویر؛ peer تست 127.0.0.1 است و معتمد نیست."""
    env = {
        **os.environ,
        "MP_DATABASE_URL": f"sqlite:///{tmp_path / 'xff.db'}",
        "MP_ENVIRONMENT": "development",
        "PYTHONPATH": str(BACKEND),
    }
    subprocess.run(
        [sys.executable, "-c", "from db.base import init_db; init_db()"],
        cwd=BACKEND,
        env=env,
        check=True,
        timeout=180,
        capture_output=True,
    )
    port = _free_port()
    flags = subprocess.run(
        ["sh", str(FLAGS_SCRIPT)], env=env, capture_output=True, text=True, check=True
    ).stdout.strip()
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--workers",
            "1",
            *shlex.split(flags),
        ],
        cwd=BACKEND,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 90
    while True:
        try:
            httpx.get(f"{base}/api/v1/health", timeout=2)
            break
        except httpx.HTTPError:
            if proc.poll() is not None or time.monotonic() > deadline:
                proc.kill()
                pytest.fail("uvicorn زنده بالا نیامد")
            time.sleep(0.5)
    try:
        yield base
    finally:
        proc.kill()
        proc.wait(timeout=30)


def test_spoofed_xff_cannot_bypass_otp_rate_limit(live_backend: str) -> None:
    """۳۰ درخواست با XFF تصادفی از peer نامعتمد ⇒ یک سهمیه؛ burst=3/s ⇒ ≥۲۷ × 429."""
    statuses = []
    with httpx.Client(timeout=10) as client:
        for i in range(30):
            r = client.post(
                f"{live_backend}/api/v1/auth/otp/request",
                json={"phone": "09121234567"},
                headers={"X-Forwarded-For": f"198.51.100.{i + 1}"},
            )
            statuses.append(r.status_code)
    assert statuses.count(429) >= 27, f"دور زدن با XFF ممکن است: {statuses}"

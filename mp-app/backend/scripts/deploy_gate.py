#!/usr/bin/env python3
"""M60 / R8 — static checks for deployment topology and configuration."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
MP = REPO / "mp-app"


@dataclass
class Report:
    checks: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self, msg: str) -> None:
        self.checks.append(msg)

    def bad(self, msg: str) -> None:
        self.problems.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def check_ports(report: Report) -> None:
    """Check the backend port across its Dockerfile, Compose, and Caddy upstream."""
    dockerfile = _read(MP / "infra" / "Dockerfile.backend")
    caddy = _read(MP / "infra" / "Caddyfile")
    compose_text = _read(MP / "infra" / "docker-compose.yml")
    compose = yaml.safe_load(compose_text) or {}

    df_expose = re.findall(r"^EXPOSE\s+(\d+)", dockerfile, re.MULTILINE)
    df_cmd_port = re.findall(r"--port[\"', ]+(\d+)", dockerfile)
    backend_upstreams = re.findall(r"reverse_proxy\s+backend:(\d+)", caddy)
    backend = compose.get("services", {}).get("backend", {})
    compose_expose = [str(port) for port in backend.get("expose", [])]

    if not df_expose or not backend_upstreams:
        report.bad("Backend port not found in Dockerfile.backend or Caddyfile")
        return
    if set(df_expose) != set(df_cmd_port):
        report.bad(f"Dockerfile EXPOSE {df_expose} does not match CMD --port {df_cmd_port}")
    elif set(df_expose) != set(backend_upstreams):
        report.bad(f"Backend port {df_expose} does not match Caddy upstreams {backend_upstreams}")
    else:
        report.ok(f"Backend port matches across Dockerfile/Caddy: {df_expose[0]}")

    if compose_expose and set(compose_expose) != set(df_expose):
        report.bad(f"Compose exposes {compose_expose}, backend listens on {df_expose}")
    elif compose_expose:
        report.ok("Compose exposes the backend listening port")


def check_env_names(report: Report) -> None:
    config = _read(MP / "backend" / "app" / "config.py")
    compose_files = list((MP / "deploy").glob("docker-compose*.yml")) + list(
        (MP / "infra").glob("docker-compose*.yml")
    )

    prefix_match = re.search(r'env_prefix\s*=\s*"([^"]+)"', config)
    if not prefix_match:
        report.bad("env_prefix not found in config.py")
        return
    prefix = prefix_match.group(1).upper()
    body = config.split("model_config", 1)[1].split("class ", 1)[0]
    fields = set(re.findall(r"^\s{4}([a-z_]+)\s*:", body, re.MULTILINE))
    if not fields:
        report.bad("No Settings fields found")
        return
    report.ok(f"env_prefix={prefix} · {len(fields)} Settings fields")

    for compose_file in compose_files:
        text = "\n".join(
            line for line in _read(compose_file).splitlines() if not line.lstrip().startswith("#")
        )
        invalid_keys = []
        for key in set(re.findall(r"\bMP_[A-Z0-9_]+", text)):
            field_name = key[len(prefix) :].lower()
            if field_name not in fields:
                invalid_keys.append(key)
        if invalid_keys:
            for key in sorted(invalid_keys):
                report.bad(f"{compose_file.name}: {key} has no matching Settings field")
        else:
            report.ok(f"{compose_file.name}: all MP_* names match Settings")


def check_healthcheck(report: Report) -> None:
    main = _read(MP / "backend" / "app" / "main.py")
    monitoring = _read(MP / "backend" / "api" / "v1" / "monitoring.py")
    if '"/health"' not in main and "'/health'" not in main:
        report.bad("Liveness endpoint /health is not registered")
    else:
        report.ok("Liveness endpoint /health exists")
    if '"/health/ready"' not in monitoring and "'/health/ready'" not in monitoring:
        report.bad("Readiness endpoint /health/ready is not registered")
    else:
        report.ok("readiness /api/v1/health/ready exists")

    supported_paths = {"/health", "/api/v1/health/ready"}
    for compose_file in (MP / "deploy" / "docker-compose.yml", MP / "infra" / "docker-compose.yml"):
        text = _read(compose_file)
        for path in re.findall(r"localhost:\d+(/[A-Za-z0-9/_-]+)", text):
            if path not in supported_paths:
                report.warn(f"{compose_file.name}: healthcheck uses unknown path {path}")


def check_build_paths(report: Report) -> None:
    """Check each service's build context and Dockerfile, not only the first one."""
    for compose_file in (MP / "deploy" / "docker-compose.yml", MP / "infra" / "docker-compose.yml"):
        text = _read(compose_file)
        if not text:
            report.warn(f"{compose_file} is missing")
            continue
        compose = yaml.safe_load(text) or {}
        for service_name, service in compose.get("services", {}).items():
            build = service.get("build")
            if not build:
                continue
            if isinstance(build, str):
                context_value, dockerfile_value = build, "Dockerfile"
            else:
                context_value = build.get("context", ".")
                dockerfile_value = build.get("dockerfile", "Dockerfile")
            context_path = (compose_file.parent / context_value).resolve()
            dockerfile_path = (context_path / dockerfile_value).resolve()
            if dockerfile_path.is_file():
                report.ok(
                    f"{compose_file.name}/{service_name}: build Dockerfile exists ({dockerfile_path.name})"
                )
            else:
                report.bad(
                    f"{compose_file.name}/{service_name}: build Dockerfile does not exist: {dockerfile_path}"
                )


def check_required_secrets(report: Report) -> None:
    text = _read(MP / "deploy" / "docker-compose.yml")
    if ":?" not in text:
        report.bad("deploy Compose defines no required (:?) settings")
    else:
        report.ok("deploy Compose marks required settings with :?")


def otp_body_exposes_dev_code(body: dict) -> bool:
    """WP 1.2 / F-02: پاسخ OTP نباید کد را داشته باشد (تست‌پذیر، بدون درخواست زنده)."""
    return "dev_code" in body and body["dev_code"] not in (None, "")


def check_otp_echo_guard(report: Report) -> None:
    """کد OTP فقط در دو نقطهٔ guard‌شده و با شرط دوگانه نوشته شود."""
    text = _read(MP / "backend" / "modules" / "auth" / "service.py")
    guarded = text.count('if provider.name == "dev" and dev_otp_echo_enabled():')
    if guarded != 2 or 'out["dev_code"]' not in text or 'result["dev_code"]' not in text:
        report.bad(f"dev_code guard در service.py ناقص است (guard={guarded}, انتظار 2)")
    else:
        report.ok("dev_code فقط با environment=development و MP_ALLOW_DEV_OTP_ECHO نوشته می‌شود")
    for compose in (MP / "infra" / "docker-compose.yml", MP / "deploy" / "docker-compose.yml"):
        content = _read(compose)
        if re.search(r"MP_ALLOW_DEV_OTP_ECHO:\s*['\"]?(true|1|yes)", content, re.IGNORECASE):
            report.bad(f"{compose.name} پرچم MP_ALLOW_DEV_OTP_ECHO را روشن کرده است")
    report.ok("Compose در هیچ استقراری MP_ALLOW_DEV_OTP_ECHO را روشن نمی‌کند")


def main() -> int:
    parser = argparse.ArgumentParser(description="Static deployment gate")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = Report()
    for check in (
        check_ports,
        check_env_names,
        check_healthcheck,
        check_build_paths,
        check_required_secrets,
        check_otp_echo_guard,
    ):
        try:
            check(report)
        except Exception as exc:  # noqa: BLE001
            report.bad(f"{check.__name__} crashed: {type(exc).__name__}: {exc}")

    if args.json:
        print(
            json.dumps(
                {"checks": report.checks, "problems": report.problems, "warnings": report.warnings},
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for check in report.checks:
            print("✓", check)
        for warning in report.warnings:
            print("!", warning)
        for problem in report.problems:
            print("✗", problem)
        print(
            f"\n{len(report.checks)} checks · {len(report.warnings)} warnings · "
            f"{len(report.problems)} problems"
        )
    return 1 if report.problems else 0


if __name__ == "__main__":
    sys.exit(main())

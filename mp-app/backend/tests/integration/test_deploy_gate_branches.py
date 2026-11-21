"""شاخه‌های خطای scripts/deploy_gate.py (WP 0.4 / F‑07).

تست رگرسیون موجود (`tests/regression/test_deploy_gate.py`) فقط مسیر موفق را روی
مخزن واقعی اجرا می‌کند. این فایل هر بررسی را روی یک درخت استقرار موقت اجرا می‌کند
و هر شاخهٔ bad/warn را با یک خطای مشخص آزمایش می‌کند.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

GATE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "deploy_gate.py"


@pytest.fixture
def dg(monkeypatch):
    name = "deploy_gate_under_test"
    spec = importlib.util.spec_from_file_location(name, GATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    # dataclasses حین تعریف کلاس، ماژول را در sys.modules می‌خواهد.
    monkeypatch.setitem(sys.modules, name, mod)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


DOCKERFILE_OK = 'FROM python:3.11\nEXPOSE 8000\nCMD ["uvicorn", "app.main:app", "--port", "8000"]\n'
CADDY_OK = "example.com {\n  reverse_proxy backend:8000\n}\n"
INFRA_COMPOSE_OK = """\
services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    expose:
      - "8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
"""
DEPLOY_COMPOSE_OK = """\
services:
  backend:
    environment:
      MP_DATABASE_URL: ${MP_DATABASE_URL:?required}
      MP_SECRET_KEY: ${MP_SECRET_KEY:?required}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/ready"]
"""
CONFIG_OK = """\
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MP_")

    database_url: str = ""
    secret_key: str = ""
"""
MAIN_OK = 'app.get("/health")\n'
MONITORING_OK = 'router.get("/health/ready")\n'
SERVICE_OK = (
    'if provider.name == "dev" and dev_otp_echo_enabled():\n'
    '    out["dev_code"] = code\n'
    'if provider.name == "dev" and dev_otp_echo_enabled():\n'
    '    result["dev_code"] = code\n'
)


def _write_tree(root: Path, **overrides: str) -> Path:
    paths = {
        "df": "infra/Dockerfile.backend",
        "caddy": "infra/Caddyfile",
        "infra": "infra/docker-compose.yml",
        "deploy": "deploy/docker-compose.yml",
        "config": "backend/app/config.py",
        "main": "backend/app/main.py",
        "monitoring": "backend/api/v1/monitoring.py",
        "service": "backend/modules/auth/service.py",
    }
    contents = {
        "df": DOCKERFILE_OK,
        "caddy": CADDY_OK,
        "infra": INFRA_COMPOSE_OK,
        "deploy": DEPLOY_COMPOSE_OK,
        "config": CONFIG_OK,
        "main": MAIN_OK,
        "monitoring": MONITORING_OK,
        "service": SERVICE_OK,
    }
    contents.update(overrides)
    files = {paths[key]: text for key, text in contents.items()}
    for rel, text in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return root


def _run(dg, root: Path, monkeypatch) -> object:
    monkeypatch.setattr(dg, "MP", root)
    report = dg.Report()
    for check in (
        dg.check_ports,
        dg.check_env_names,
        dg.check_healthcheck,
        dg.check_build_paths,
        dg.check_required_secrets,
        dg.check_otp_echo_guard,
    ):
        check(report)
    return report


def test_clean_tree_has_no_problems(dg, tmp_path, monkeypatch) -> None:
    report = _run(dg, _write_tree(tmp_path), monkeypatch)
    assert report.problems == []
    assert report.warnings == []
    assert len(report.checks) >= 6


def test_port_mismatch_between_expose_and_cmd(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(
        tmp_path,
        df='EXPOSE 8000\nCMD ["x", "--port", "8001"]\n',
    )
    report = _run(dg, root, monkeypatch)
    assert any("does not match CMD --port" in p for p in report.problems)


def test_port_mismatch_with_caddy_upstream(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(tmp_path, caddy="reverse_proxy backend:9000\n")
    report = _run(dg, root, monkeypatch)
    assert any("does not match Caddy upstreams" in p for p in report.problems)


def test_compose_expose_disagrees_with_dockerfile(dg, tmp_path, monkeypatch) -> None:
    compose = INFRA_COMPOSE_OK.replace('"8000"', '"9999"')
    report = _run(dg, _write_tree(tmp_path, infra=compose), monkeypatch)
    assert any("Compose exposes" in p for p in report.problems)


def test_missing_backend_port_is_reported_and_stops_port_check(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(tmp_path, df="FROM python:3.11\n")
    report = _run(dg, root, monkeypatch)
    assert report.problems == ["Backend port not found in Dockerfile.backend or Caddyfile"]


def test_unknown_env_name_in_compose_is_a_problem(dg, tmp_path, monkeypatch) -> None:
    deploy = DEPLOY_COMPOSE_OK + "      MP_BOGUS_KEY: x\n"
    report = _run(dg, _write_tree(tmp_path, deploy=deploy), monkeypatch)
    assert any("MP_BOGUS_KEY has no matching Settings field" in p for p in report.problems)


def test_missing_env_prefix_is_a_problem(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(tmp_path, config="class Settings:\n    pass\n")
    report = _run(dg, root, monkeypatch)
    assert "env_prefix not found in config.py" in report.problems


def test_settings_without_fields_is_a_problem(dg, tmp_path, monkeypatch) -> None:
    config = 'model_config = SettingsConfigDict(env_prefix="MP_")\n'
    root = _write_tree(tmp_path, config=config)
    report = _run(dg, root, monkeypatch)
    assert "No Settings fields found" in report.problems


def test_missing_liveness_and_readiness_endpoints(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(
        tmp_path,
        main="# no health route\n",
        monitoring="# no ready route\n",
    )
    report = _run(dg, root, monkeypatch)
    assert "Liveness endpoint /health is not registered" in report.problems
    assert "Readiness endpoint /health/ready is not registered" in report.problems


def test_unknown_healthcheck_path_is_only_a_warning(dg, tmp_path, monkeypatch) -> None:
    compose = INFRA_COMPOSE_OK.replace("/health", "/metrics")
    report = _run(dg, _write_tree(tmp_path, infra=compose), monkeypatch)
    assert any("unknown path /metrics" in w for w in report.warnings)
    assert report.problems == []


def test_missing_build_dockerfile_is_a_problem(dg, tmp_path, monkeypatch) -> None:
    compose = INFRA_COMPOSE_OK.replace("dockerfile: Dockerfile.backend", "dockerfile: Nope")
    report = _run(dg, _write_tree(tmp_path, infra=compose), monkeypatch)
    assert any("build Dockerfile does not exist" in p for p in report.problems)


def test_string_build_form_uses_default_dockerfile(dg, tmp_path, monkeypatch) -> None:
    compose = "services:\n  backend:\n    build: .\n"
    root = _write_tree(tmp_path, infra=compose)
    (root / "infra" / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
    report = _run(dg, root, monkeypatch)
    assert any("build Dockerfile exists (Dockerfile)" in c for c in report.checks)


def test_missing_compose_file_is_a_warning(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(tmp_path)
    (root / "infra" / "docker-compose.yml").unlink()
    report = _run(dg, root, monkeypatch)
    assert any("is missing" in w for w in report.warnings)


def test_required_secrets_marker_is_enforced(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(tmp_path, deploy="services: {}\n")
    report = _run(dg, root, monkeypatch)
    assert "deploy Compose defines no required (:?) settings" in report.problems


def test_otp_echo_guard_count_mismatch(dg, tmp_path, monkeypatch) -> None:
    root = _write_tree(tmp_path, service='result["dev_code"] = 1\n')
    report = _run(dg, root, monkeypatch)
    assert any("dev_code guard در service.py ناقص است" in p for p in report.problems)


def test_otp_echo_flag_enabled_in_compose_is_a_problem(dg, tmp_path, monkeypatch) -> None:
    deploy = DEPLOY_COMPOSE_OK + "      MP_ALLOW_DEV_OTP_ECHO: 'true'\n"
    report = _run(dg, _write_tree(tmp_path, deploy=deploy), monkeypatch)
    assert any("پرچم MP_ALLOW_DEV_OTP_ECHO را روشن کرده است" in p for p in report.problems)


@pytest.mark.parametrize(
    ("body", "exposed"),
    [
        ({"dev_code": "123456"}, True),
        ({"dev_code": ""}, False),
        ({"dev_code": None}, False),
        ({}, False),
    ],
)
def test_otp_body_exposes_dev_code(dg, body, exposed) -> None:
    assert dg.otp_body_exposes_dev_code(body) is exposed


def test_check_crash_is_reported_not_raised(dg, tmp_path, monkeypatch, capsys) -> None:
    # YAML نامعتبر در Compose، check_ports را منفجر می‌کند؛ main باید آن را گزارش کند.
    root = _write_tree(tmp_path, infra="services: [\n")
    monkeypatch.setattr(dg, "MP", root)
    monkeypatch.setattr(sys, "argv", ["deploy_gate.py", "--json"])
    rc = dg.main()
    out = json.loads(capsys.readouterr().out)
    assert rc == 1
    assert any(p.startswith("check_ports crashed:") for p in out["problems"])


def test_main_text_output_and_exit_code(dg, tmp_path, monkeypatch, capsys) -> None:
    root = _write_tree(tmp_path)
    monkeypatch.setattr(dg, "MP", root)
    monkeypatch.setattr(sys, "argv", ["deploy_gate.py"])
    assert dg.main() == 0
    text = capsys.readouterr().out
    assert "✓" in text and "0 problems" in text

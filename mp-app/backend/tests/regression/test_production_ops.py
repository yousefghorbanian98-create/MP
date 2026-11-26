"""Regression gates for production configuration and Compose topology."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from app.config import Settings

BACKEND = Path(__file__).resolve().parents[2]
MP = BACKEND.parent


def valid_production_settings(**overrides) -> Settings:
    values = {
        "environment": "production",
        "secret_key": "S" * 64,
        "biometric_key": base64.b64encode(b"B" * 32).decode("ascii"),
        "sms_provider": "kavenegar",
        "sms_api_url": "https://sms.example.test/v1",
        "sms_api_key": "sms-test-key",
        "sms_originator": "1000000000",
        "valkey_url": "redis://valkey:6379/0",
        "cors_origins": "https://studio.example.test",
        "payment_gateway": "manual",
        "payment_sandbox": False,
        "trusted_proxies": "172.18.0.2",  # WP 1.1 / F-01: الزامی در production
    }
    values.update(overrides)
    return Settings(**values)


def test_complete_production_settings_are_accepted() -> None:
    assert valid_production_settings().environment == "production"
    assert (
        valid_production_settings(
            sms_provider="webmagfa",
            sms_api_url="https://sms.example.test/api",
            sms_api_key="",
            sms_username="account",
            sms_password="password",
            sms_originator="1000000000",
        ).sms_provider
        == "webmagfa"
    )


@pytest.mark.parametrize(
    ("override", "expected"),
    [
        ({"secret_key": "short"}, "MP_SECRET_KEY"),
        ({"biometric_key": "not-base64"}, "MP_BIOMETRIC_KEY"),
        ({"sms_provider": "dev"}, "MP_SMS_PROVIDER"),
        ({"sms_api_url": "http://sms.example.test"}, "MP_SMS_API_URL"),
        ({"sms_api_url": "https://:password@sms.example.test"}, "MP_SMS_API_URL"),
        ({"valkey_url": "redis://localhost:6379/0"}, "MP_VALKEY_URL"),
        ({"cors_origins": "*"}, "MP_CORS_ORIGINS"),
        ({"cors_origins": "https://user:password@studio.example.test"}, "MP_CORS_ORIGINS"),
        ({"payment_gateway": "mock"}, "MP_PAYMENT_GATEWAY"),
        ({"payment_gateway": "sandbox"}, "MP_PAYMENT_GATEWAY"),
        ({"payment_sandbox": True}, "MP_PAYMENT_SANDBOX"),
    ],
)
def test_insecure_production_settings_fail_closed(override: dict, expected: str) -> None:
    with pytest.raises(ValidationError) as exc:
        valid_production_settings(**override)
    assert expected in str(exc.value)


def test_jwt_and_biometric_keys_cannot_be_the_same_material() -> None:
    shared_material = base64.b64encode(b"S" * 32).decode("ascii")
    with pytest.raises(ValidationError) as exc:
        valid_production_settings(
            secret_key=shared_material,
            biometric_key=shared_material,
        )
    assert "MP_BIOMETRIC_KEY" in str(exc.value)


def test_configuration_errors_do_not_echo_secret_values() -> None:
    marker = "sms-secret-must-not-appear-in-errors"
    with pytest.raises(ValidationError) as exc:
        valid_production_settings(sms_provider="dev", sms_api_key=marker)
    assert marker not in str(exc.value)


def test_unknown_sms_provider_is_rejected_by_settings() -> None:
    with pytest.raises(ValidationError):
        Settings(environment="development", sms_provider="unknown")


def _compose(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(config, dict)
    return config


@pytest.mark.parametrize(
    "compose_path",
    [MP / "deploy" / "docker-compose.yml", MP / "infra" / "docker-compose.yml"],
)
def test_production_compose_is_fail_closed_and_valkey_backed(compose_path: Path) -> None:
    config = _compose(compose_path)
    services = config["services"]
    backend = services["backend"]
    environment = backend["environment"]

    assert environment["MP_ENVIRONMENT"] == "production"
    for required in (
        "MP_SECRET_KEY",
        "MP_BIOMETRIC_KEY",
        "MP_CORS_ORIGINS",
        "MP_SMS_PROVIDER",
        "MP_PAYMENT_GATEWAY",
        "MP_METRICS_TOKEN",
        "MP_TRUSTED_PROXIES",
    ):
        assert ":?" in environment[required], f"{compose_path}: {required} must be required"
    assert environment["MP_VALKEY_URL"] == "redis://valkey:6379/0"
    prometheus_environment = services["prometheus"]["environment"]
    assert prometheus_environment["MP_METRICS_TOKEN"] == environment["MP_METRICS_TOKEN"]
    assert ":?" in backend["image"] and "IMAGE_OWNER" in backend["image"]
    assert ":?" in backend["image"] and "IMAGE_TAG" in backend["image"]
    assert services["studio"]["image"] == backend["image"].replace("mp-backend", "mp-studio")
    assert services["backup"]["image"] == backend["image"]
    assert backend["depends_on"]["valkey"]["condition"] == "service_healthy"
    multiproc_dir = environment["PROMETHEUS_MULTIPROC_DIR"]
    assert multiproc_dir.startswith("/") and multiproc_dir.endswith("/prometheus-multiproc")
    assert multiproc_dir in backend["tmpfs"]

    for service_name in ("backend", "studio"):
        build = services[service_name]["build"]
        context = (compose_path.parent / build["context"]).resolve()
        assert (context / build["dockerfile"]).is_file(), (
            f"{compose_path}: {service_name} build path"
        )
    assert "studio" in services and "backup" in services
    assert "prometheus" in services and "valkey-exporter" in services
    assert not backend.get("ports")
    assert not services["valkey"].get("ports")
    assert "noeviction" in services["valkey"]["command"]
    assert services["prometheus"]["ports"][0].startswith("127.0.0.1:")


def test_production_environment_template_leaves_proxy_and_metrics_values_unset() -> None:
    template = (BACKEND / ".env.example").read_text(encoding="utf-8").splitlines()
    for name in ("MP_TRUSTED_PROXIES", "MP_METRICS_TOKEN", "STUDIO_TRUSTED_PROXY"):
        assignments = [line for line in template if line.startswith(f"{name}=")]
        assert assignments == [f"{name}="]


@pytest.mark.parametrize(
    ("compose_path", "proxy_service", "proxy_address"),
    [
        (MP / "deploy" / "docker-compose.yml", "studio", "${MP_STUDIO_IP:-172.30.0.3}"),
        (MP / "infra" / "docker-compose.yml", "caddy", "${MP_CADDY_IP:-172.30.0.4}"),
    ],
)
def test_compose_trusts_the_statically_addressed_immediate_proxy(
    compose_path: Path, proxy_service: str, proxy_address: str
) -> None:
    config = _compose(compose_path)
    network = config["networks"]["default"]
    assert network["ipam"]["config"][0]["subnet"] == "${MP_COMPOSE_SUBNET:-172.30.0.0/24}"

    services = config["services"]
    assert (
        services["backend"]["networks"]["default"]["ipv4_address"] == "${MP_BACKEND_IP:-172.30.0.2}"
    )
    assert services[proxy_service]["networks"]["default"]["ipv4_address"] == proxy_address
    trusted = services["backend"]["environment"]["MP_TRUSTED_PROXIES"]
    assert trusted.startswith("${MP_TRUSTED_PROXIES:?")
    assert proxy_address.rsplit(":-", maxsplit=1)[-1].rstrip("}") in trusted


def test_studio_nginx_sanitizes_forwarded_ip_only_from_configured_upstream() -> None:
    compose = _compose(MP / "deploy" / "docker-compose.yml")
    studio_environment = compose["services"]["studio"]["environment"]
    assert studio_environment["STUDIO_TRUSTED_PROXY"].startswith("${STUDIO_TRUSTED_PROXY:?")
    assert studio_environment["NGINX_ENVSUBST_FILTER"] == "^STUDIO_TRUSTED_PROXY$"
    infra_studio_environment = _compose(MP / "infra" / "docker-compose.yml")["services"]["studio"][
        "environment"
    ]
    assert (
        infra_studio_environment["STUDIO_TRUSTED_PROXY"] == "${STUDIO_TRUSTED_PROXY:-127.0.0.1/32}"
    )

    nginx = (MP / "studio" / "nginx.conf").read_text(encoding="utf-8")
    assert "set_real_ip_from ${STUDIO_TRUSTED_PROXY};" in nginx
    assert "real_ip_header X-Forwarded-For;" in nginx
    assert "real_ip_recursive on;" in nginx
    assert "proxy_set_header X-Forwarded-For $remote_addr;" in nginx
    assert "proxy_set_header X-Forwarded-For $http_x_forwarded_for;" not in nginx
    dockerfile = (MP / "studio" / "Dockerfile").read_text(encoding="utf-8")
    assert "/etc/nginx/templates/default.conf.template" in dockerfile


@pytest.mark.parametrize(
    "compose_path",
    [MP / "deploy" / "docker-compose.yml", MP / "infra" / "docker-compose.yml"],
)
def test_backup_uses_the_live_database_and_runs_immediately(compose_path: Path) -> None:
    config = _compose(compose_path)
    backup = config["services"]["backup"]
    command = " ".join(backup["command"])
    assert "backup.py backup --db /data/mp.db --out /backups" in command
    assert command.index("backup.py backup") < command.index("sleep 86400")
    assert "sleep 3600" in command  # retry visibly instead of silently dying
    assert backup["image"] == config["services"]["backend"]["image"]
    assert backup["pull_policy"] == "never"
    data_mounts = " ".join(backup["volumes"])
    assert "mp-data:/data:ro" in data_mounts
    assert "mp-backups:/backups" in data_mounts


def test_infra_backend_image_copies_runtime_packages_and_backup_inputs() -> None:
    dockerfile = (MP / "infra" / "Dockerfile.backend").read_text(encoding="utf-8")
    for directory in (
        "app",
        "api",
        "modules",
        "db",
        "security",
        "jobs",
        "cache",
        "engine",
        "eval",
        "data",
        "scripts",
        "static",
    ):
        assert f"COPY mp-app/backend/{directory} " in dockerfile
    assert "COPY mp-app/shared/design-tokens.json" in dockerfile


def test_infra_caddy_requires_real_domain_and_serves_the_full_stack() -> None:
    config = _compose(MP / "infra" / "docker-compose.yml")
    services = config["services"]
    environment = services["caddy"]["environment"]
    assert ":?" in environment["PUBLIC_DOMAIN"]
    assert ":?" in environment["TLS_EMAIL"]
    assert services["caddy"]["depends_on"]["studio"]["condition"] == "service_started"
    assert services["backend"]["expose"] == ["8000"]
    assert services["prometheus"]["environment"]["PROMETHEUS_BACKEND_PORT"] == "8000"
    assert services["studio"]["expose"] == ["80"]
    assert "mp-backups" in config["volumes"]
    caddyfile = (MP / "infra" / "Caddyfile").read_text(encoding="utf-8")
    assert "{$PUBLIC_DOMAIN}" in caddyfile
    assert "{$TLS_EMAIL}" in caddyfile
    assert "reverse_proxy backend:8000" in caddyfile
    assert "reverse_proxy studio:80" in caddyfile

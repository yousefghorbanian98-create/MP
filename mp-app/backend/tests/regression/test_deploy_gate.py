"""M60/R8 — گیت استقرار: تست خودِ قاعده + وضعیت واقعی مخزن.

گیت استقرار بدون تست، همان سرنوشت همهٔ گیت‌های بی‌تست را دارد: یک روز
قرمز می‌شود، کسی خاموشش می‌کند. این‌جا هم قاعده روی ورودی ساختگی سنجیده
می‌شود و هم مخزن واقعی.

یافتهٔ واقعی که این گیت داد: `deploy/docker-compose.yml` متغیر
`MP_JWT_SECRET` را اجباری می‌کرد ولی هیچ فیلدی در Settings با آن نام نبود
(`env_prefix=MP_` + فیلد `secret_key` ← `MP_SECRET_KEY`). یعنی در تولید،
کلید JWT مقدار پیش‌فرض توسعه می‌ماند — توکن جعل‌شدنی. حالا هر دو سمت
هم‌خوان‌اند و تست پایین همین هم‌خوانی را قفل می‌کند.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
GATE = BACKEND / "scripts" / "deploy_gate.py"


def _load():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    spec = importlib.util.spec_from_file_location("deploy_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # dataclassها __module__ را در sys.modules می‌جوند؛ بدون ثبت، import سقوط می‌کند
    # (همین اشتباه یک‌بار در تست dart_gate هم رخ داد).
    sys.modules["deploy_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()


def test_gate_runs_clean_on_repo() -> None:
    report = gate.Report()
    for fn in (
        gate.check_ports,
        gate.check_env_names,
        gate.check_healthcheck,
        gate.check_build_paths,
        gate.check_required_secrets,
    ):
        fn(report)
    assert report.problems == [], "\n".join(report.problems)
    assert len(report.checks) >= 8, f"بررسی‌ها کم اجرا شدند: {report.checks}"


def test_port_check_catches_drift() -> None:
    """اگر Caddy به پورت دیگری اشاره کند، گیت باید قرمز شود."""
    original = gate._read
    try:

        def fake_read(p: Path) -> str:
            text = original(p)
            if p.name == "Caddyfile":
                return text.replace("backend:8751", "backend:9999")
            return text

        gate._read = fake_read
        report = gate.Report()
        gate.check_ports(report)
    finally:
        gate._read = original
    assert any("Caddy" in p or "کدی" in p for p in report.problems), report.problems


def test_env_name_check_catches_wrong_prefix() -> None:
    """نام env بی‌اثر (مثل MP_JWT_SECRET) باید گرفته شود."""
    original = gate._read
    target = gate.MP / "deploy" / "docker-compose.yml"
    try:

        def fake_read(p: Path) -> str:
            text = original(p)
            if p == target:
                return text.replace(
                    "MP_SECRET_KEY: ${MP_SECRET_KEY", "MP_WRONG_NAME: ${MP_WRONG_NAME"
                )
            return text

        gate._read = fake_read
        report = gate.Report()
        gate.check_env_names(report)
    finally:
        gate._read = original
    assert any("MP_WRONG_NAME" in p for p in report.problems), report.problems


def test_compose_secret_name_matches_settings_field() -> None:
    """قفل مستقیم: compose و Settings باید روی یک نام توافق داشته باشند.

    این تست به گیت وابسته نیست؛ اگر روزی گیت حذف شود، باگ برنمی‌گردد.
    """
    from app.config import settings

    compose = (gate.MP / "deploy" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "MP_SECRET_KEY" in compose, "compose باید MP_SECRET_KEY بدهد"
    assert settings.model_fields.get("secret_key") is not None
    env_name = "MP_" + "secret_key".upper()
    assert env_name == "MP_SECRET_KEY"

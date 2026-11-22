"""WP 4.1 / F‑15 — مشخصه‌یابی (characterization) رفتار validate_production_configuration.

هدف: شکستن تابع به اعتبارسنج‌های خانوادگی نباید هیچ خروجیِ پیام یا ترتیبی را تغییر دهد.
golden روی HEAD پیش از شکستن ساخته شد (اسکریپت: scripts/... نیست؛ ساخت با همین ماتریس
و seed ثابت در `_matrix()`). این آزمون refactor را قفل می‌کند؛ رفتار جدیدی اضافه نمی‌کند.
"""

from __future__ import annotations

import base64
import json
import random
from pathlib import Path

import pytest

from app.config import Settings

GOLDEN = Path(__file__).parent / "fixtures" / "wp41_config_golden.json"
SAMPLES = 600
SEED = 41


def _matrix(n: int = SAMPLES, seed: int = SEED):
    rnd = random.Random(seed)
    secret_good = "s" * 40
    biometric_ok = base64.b64encode(b"b" * 32).decode()
    axes = {
        "secret_key": ["", "short", "change-me-please-000000000000000000000000", secret_good, "x" * 16],
        "biometric_key": ["", "not base64!", base64.b64encode(b"c" * 16).decode(), biometric_ok, secret_good],
        "sms_provider": ["dev", "webmagfa", "kavenegar"],
        "allow_dev_otp_echo": [False, True],
        "sms_api_url": ["", "http://sms.example.ir", "https://sms.example.ir", "https://u:p@sms.example.ir", "not a url"],
        "sms_api_key": ["", "k"],
        "sms_username": ["", "u"],
        "sms_password": ["", "p"],
        "sms_originator": ["", "3000"],
        "trusted_proxies": ["", "10.0.0.0/8", "10.0.0.1, bad", "10.0.0.1", " , "],
        "valkey_url": ["redis://localhost:6379/0", "redis://valkey.internal:6379/0", "http://valkey:1", "", "rediss://10.1.2.3:6380/0"],
        "cors_origins": ["", "*", "https://app.example.ir", "http://app.example.ir", "https://a.ir/path", "https://a.ir,https://b.ir", "https://localhost"],
        "payment_gateway": ["manual", "mock", "sandbox"],
        "payment_sandbox": [True, False],
    }
    base = {
        "secret_key": secret_good,
        "biometric_key": biometric_ok,
        "sms_provider": "webmagfa",
        "allow_dev_otp_echo": False,
        "sms_api_url": "https://sms.example.ir",
        "sms_api_key": "k",
        "sms_username": "u",
        "sms_password": "p",
        "sms_originator": "3000",
        "trusted_proxies": "10.0.0.0/8",
        "valkey_url": "redis://valkey.internal:6379/0",
        "cors_origins": "https://app.example.ir",
        "payment_gateway": "manual",
        "payment_sandbox": False,
    }
    out = []
    for _ in range(n):
        case = dict(base)
        for key in rnd.sample(list(axes), k=rnd.randint(0, 3)):
            case[key] = rnd.choice(axes[key])
        out.append(case)
    return out


def _outcome(kwargs: dict) -> str:
    try:
        Settings(_env_file=None, environment="production", **kwargs)
    except ValueError as exc:
        return "ERR:" + str(exc)
    except Exception as exc:  # noqa: BLE001 — خطای اعتبارسنجی Pydantic هم ثبت شود
        return "OTHER:" + type(exc).__name__
    return "OK"


def test_outcomes_match_golden():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    cases = _matrix()
    assert len(golden) == len(cases) == SAMPLES
    mismatches = []
    for case, expected in zip(cases, golden):
        got = _outcome(case)
        if got != expected["outcome"]:
            mismatches.append((case, expected["outcome"], got))
    assert mismatches == [], f"{len(mismatches)} تفاوت؛ نمونه: {mismatches[:2]}"


def test_matrix_covers_both_outcomes():
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    kinds = {e["outcome"].split(":", 1)[0] for e in golden}
    assert "ERR" in kinds and "OK" in kinds

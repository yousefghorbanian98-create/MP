"""M60 / R15 — تست قواعد بازرسی APK بدون نیاز به APK یا androguard.

چرا تست جدا: `apk_audit.py` در `mp-app/client/tools` است (نه داخل پکیج
بک‌اند)، پس pytest آن را با importlib بار می‌کند. تابع `check_policy` داده‌ی
محور است: با یک دیکشنری «بستهٔ سالم» شروع می‌کنیم و هر قاعده را با خراب کردن
یک فیلد می‌سنجیم. این‌طوری می‌شود مطمئن بود گیت در CI واقعاً چیزی را رد می‌کند
و صرفاً یک فایل تزئینی نیست.

اگر androguard نصب نباشد، تست‌های خودِ بازرسی فایل skip می‌شوند (نه fail) —
CI بک‌اند نباید به یک ابزار جانبی وابسته شود.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

AUDIT = Path(__file__).resolve().parents[3] / "client" / "tools" / "apk_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("apk_audit", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


if not AUDIT.exists():  # pragma: no cover
    pytest.skip("apk_audit.py نیست", allow_module_level=True)

audit = _load()


def healthy(**over) -> dict:
    base = {
        "permissions": [
            "android.permission.INTERNET",
            "ir.muscleparadise.mp_client.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION",
        ],
        "debuggable": None,
        "allowBackup": "false",
        "minSdk": 24,
        "targetSdk": 36,
        "usesCleartextTraffic": None,
        "hasNetworkSecurityConfig": True,
        "signature": {"v1": False, "v2": True, "v3": False, "valid": True},
        "sha256_file_match": True,
    }
    base.update(over)
    return base


def test_healthy_package_passes():
    r = audit.check_policy(healthy())
    assert r["pass"] is True, r["failures"]
    assert r["failures"] == []


@pytest.mark.parametrize(
    "over,needle",
    [
        ({"permissions": []}, "INTERNET"),
        ({"permissions": ["android.permission.INTERNET", "android.permission.CAMERA"]}, "CAMERA"),
        (
            {"permissions": ["android.permission.INTERNET", "android.permission.READ_SMS"]},
            "READ_SMS",
        ),
        ({"debuggable": "true"}, "debuggable"),
        ({"minSdk": 21}, "minSdk"),
        ({"targetSdk": 30}, "targetSdk"),
        ({"signature": {"v1": False, "v2": False, "v3": False, "valid": False}}, "امضا"),
        ({"signature": {"v1": True, "v2": False, "v3": False, "valid": True}}, "v2/v3"),
        ({"sha256_file_match": False}, "sha256"),
    ],
)
def test_policy_catches_regressions(over, needle):
    r = audit.check_policy(healthy(**over))
    assert r["pass"] is False
    assert any(needle in f for f in r["failures"]), r["failures"]


def test_allow_backup_is_warning_not_failure():
    r = audit.check_policy(healthy(allowBackup="true"))
    assert r["pass"] is True
    assert any("allowBackup" in w for w in r["warnings"])


def test_cleartext_is_warning_only():
    """معماری «سرور محلی روی LAN» cleartext را لازم دارد؛ نباید fail شود."""
    r = audit.check_policy(healthy(hasNetworkSecurityConfig=True))
    assert r["pass"] is True
    assert any("cleartext" in w for w in r["warnings"])

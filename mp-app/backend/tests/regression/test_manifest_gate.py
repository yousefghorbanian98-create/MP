"""M60 — تست گیت مانیفست اندروید.

این گیت از یک شکست واقعی زاده شد: اجرای ۴۳۸۲۸۴۵۴۰۲۱ در `lintVitalRelease`
شکست، چون `android:debuggable="false"` در سورس مانیفست بود. دو درس:

  ۱) «سخت‌کردن» مانیفست با ویژگی‌ای که Gradle خودش می‌گذارد، اپ را امن‌تر
     نمی‌کند و انتشار را می‌شکند.
  ۲) گیت باید روی نمونهٔ «بد» هم قرمز شود، وگرنه تزئینی است.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

CLIENT = Path(__file__).resolve().parents[3] / "client"
GATE = CLIENT / "tools" / "manifest_gate.py"


def _load():
    spec = importlib.util.spec_from_file_location("manifest_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["manifest_gate"] = mod
    spec.loader.exec_module(mod)
    return mod


gate = _load()


def _manifest(tmp_path: Path, application_attrs: str, comments: str = "") -> Path:
    p = tmp_path / "AndroidManifest.xml"
    p.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        f"{comments}"
        f"<application {application_attrs}></application>"
        "</manifest>",
        encoding="utf-8",
    )
    return p


def test_repo_manifest_is_clean() -> None:
    """مانیفست واقعی مخزن نباید یافته داشته باشد."""
    for path in gate.MANIFESTS:
        if not path.is_file():
            pytest.skip("مانیفست اندروید در مخزن نیست")
        assert gate.check(path) == []


def test_hardcoded_debuggable_is_caught(tmp_path: Path) -> None:
    """رگرسیون دقیقاً همان چیزی که بیلد release را شکست."""
    path = _manifest(tmp_path, 'android:allowBackup="false" android:debuggable="false"')
    rules = [f["rule"] for f in gate.check(path)]
    assert "HardcodedDebugMode" in rules


def test_missing_allowbackup_false_is_caught(tmp_path: Path) -> None:
    path = _manifest(tmp_path, 'android:label="x"')
    rules = [f["rule"] for f in gate.check(path)]
    assert "AllowBackup" in rules


def test_double_dash_inside_xml_comment_is_caught(tmp_path: Path) -> None:
    """باگ واقعی M45: `--` در کامنت XML، پارس را می‌شکند و بیلد را متوقف می‌کند."""
    path = _manifest(
        tmp_path,
        'android:allowBackup="false"',
        comments="<!-- اجرا با --dart-define=MP_API -->",
    )
    found = gate.check(path)
    # ElementTree اصلاً پارس نمی‌کند؛ یا خطای xml یا یافتهٔ XmlComment
    assert found, "کامنت نامعتبر باید یافته بدهد"
    assert any(f["rule"] in ("xml", "XmlComment") for f in found), found


def test_sensitive_permission_is_caught(tmp_path: Path) -> None:
    p = tmp_path / "AndroidManifest.xml"
    p.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        '<uses-permission android:name="android.permission.READ_SMS"/>'
        '<application android:allowBackup="false"></application>'
        "</manifest>",
        encoding="utf-8",
    )
    assert any(f["rule"] == "SensitivePermission" for f in gate.check(p))


def test_clean_manifest_passes(tmp_path: Path) -> None:
    """کنترل مثبت: مانیفست درست نباید هیچ یافته‌ای بدهد."""
    path = _manifest(tmp_path, 'android:allowBackup="false" android:label="mp_client"')
    assert gate.check(path) == []

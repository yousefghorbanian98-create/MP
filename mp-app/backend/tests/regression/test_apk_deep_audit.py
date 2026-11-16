"""M60/R-ApkDeep — تست خودِ بازرسی عمیق APK.

چرا: این گیت به سه چیز بیرونی وابسته است (java، apktool.jar، فایل APK) و
دقیقاً همین باعث می‌شود بی‌صدا خاموش شود — یا همیشه سبز بماند یا همیشه قرمز
و بعد کسی از CI برش دارد. تست‌ها دو چیز را می‌بندند:

  ۱) قوانین (`_is_private`، الگوهای راز، مجوزهای مشکوک) روی نمونهٔ ساختگی
  ۲) خود گیت روی APK واقعی — اگر ابزار غایب باشد skip می‌شود، نه fail

اگر روزی `apk-revise`/`jdk4py` در محیط نبود، تست skip می‌شود و این طبیعی است؛
ولی وقتی ابزار هست، نتیجه باید واقعی باشد.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

CLIENT = Path(__file__).resolve().parents[3] / "client"
GATE = CLIENT / "tools" / "apk_deep_audit.py"


def _load():
    spec = importlib.util.spec_from_file_location("apk_deep_audit", GATE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["apk_deep_audit"] = mod  # پیش از exec_module تا dataclass/typing نشکند
    spec.loader.exec_module(mod)
    return mod


gate = _load()


# ── قوانین، بدون نیاز به ابزار بیرونی ──
@pytest.mark.parametrize(
    "host,expected",
    [
        ("localhost", True),
        ("127.0.0.1", True),
        ("10.0.2.2", True),
        ("192.168.1.10", True),
        ("172.16.0.5", True),
        ("172.31.255.254", True),
        ("8.8.8.8", False),
        ("172.32.0.1", False),  # یک اکتت بیرون از /12
        ("example.com", False),
        ("192.169.0.1", False),
        ("", False),
    ],
)
def test_private_host_rule(host: str, expected: bool) -> None:
    """قانون «cleartext فقط در LAN» باید هم بپذیرد هم رد کند."""
    assert gate._is_private(host) is expected


@pytest.mark.parametrize(
    "text",
    [
        "sk_live_abcdefgh12345678",
        "AKIAABCDEFGHIJKLMNOP",
        "-----BEGIN RSA PRIVATE KEY-----",
        'api_key = "abcdefghijklmnop1234"',
        'secret: "abcdefghijklmnopqrstuvwx"',
    ],
)
def test_secret_patterns_catch_real_shapes(text: str) -> None:
    """هر الگو باید دست‌کم یک راز واقعی‌شکل را بگیرد — وگرنه تزئینی است."""
    assert any(p.search(text) for p in gate.SECRET_PATTERNS), text


def test_secret_patterns_do_not_fire_on_normal_dart_strings() -> None:
    """مثبت کاذب یعنی گیت خاموش می‌شود؛ رشته‌های عادی نباید بگیرند."""
    normal = [
        "https://api.muscleparadise.ir/api/v1",
        "Content-Type: application/json",
        "Bearer ${token}",
        "mp_token",
    ]
    for text in normal:
        assert not any(p.search(text) for p in gate.SECRET_PATTERNS), text


def test_blocker_message_names_the_exact_missing_thing() -> None:
    """درس این جلسه: «نمی‌شود» بی‌فایده است؛ پیام باید نام دقیق بدهد."""
    for candidate in gate.APKTOOL_JAR_CANDIDATES:
        if Path(candidate).is_file():
            pytest.skip("apktool موجود است")
    with pytest.raises(gate.Blocker) as e:
        gate.find_apktool()
    assert "apk-revise" in str(e.value) and "2.7" in str(e.value)


# ── خود گیت روی APK واقعی ──
def _tools_available() -> bool:
    try:
        java = gate.find_java()
        jar = gate.find_apktool()
        return gate.apktool_version(java, jar) >= gate.MIN_APKTOOL
    except gate.Blocker:
        return False


def test_real_apks_pass_the_deep_audit() -> None:
    """روی خروجی واقعی: بدون مجوز حساس، بدون debuggable، بدون راز در payload."""
    if not _tools_available():
        pytest.skip("java/apktool در این محیط نیست")
    apks = sorted(gate.RELEASE.glob("app-*-release.apk"))
    if not apks:
        pytest.skip("APK release در مخزن نیست")

    java, jar = gate.find_java(), gate.find_apktool()
    version = ".".join(map(str, gate.apktool_version(java, jar)))
    import tempfile

    for apk in apks:
        with tempfile.TemporaryDirectory() as td:
            tree = Path(td) / "d"
            gate.decode(java, jar, apk, tree)
            result = gate.audit_decoded(tree, apk, version)
        assert result["decoded_files"] > 100, result
        assert not result["payload_findings"], result["payload_findings"]
        assert result["flags"]["debuggable"] is False
        assert result["flags"]["allow_backup"] is False
        assert not set(result["permissions"]) & gate.SUSPICIOUS_PERMISSIONS
        # کد دارت نباید ارسال شده باشد (release باید AOT باشد، نه kernel)
        assert not result["dart_source_shipped"], result["dart_source_shipped"]


# ── باگ واقعی در خودِ ابزار: regex با فرض ترتیب ویژگی‌ها ──
def test_exported_components_parsed_regardless_of_attribute_order(tmp_path) -> None:
    """نسخهٔ اول ابزار با regex کار می‌کرد و فرض داشت `android:name` اول می‌آید.

    در مانیفست واقعی (بازنویسی‌شده با apktool) ترتیب برعکس است، پس فهرست
    exported **همیشه خالی** برمی‌گشت در حالی که شمارندهٔ درشت ۲ می‌داد.
    """
    mf = tmp_path / "AndroidManifest.xml"
    mf.write_text(
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android">'
        "<application>"
        '<activity android:exported="true" android:name="com.x.Main">'
        "<intent-filter>"
        '<action android:name="android.intent.action.MAIN"/>'
        '<category android:name="android.intent.category.LAUNCHER"/>'
        "</intent-filter></activity>"
        '<receiver android:exported="true" android:permission="android.permission.DUMP"'
        ' android:name="com.x.SafeReceiver"/>'
        '<receiver android:exported="true" android:name="com.x.LeakyReceiver"/>'
        "</application></manifest>",
        encoding="utf-8",
    )
    acts, recvs, unprotected = gate._exported_components(mf)
    assert acts == ["com.x.Main"]
    assert recvs == ["com.x.SafeReceiver", "com.x.LeakyReceiver"]
    # activity لانچر exported بودنش اجباری است → محافظ لازم ندارد
    # receiver با permission محافظت‌شده است → فقط LeakyReceiver یافته می‌شود
    assert unprotected == ["receiver:com.x.LeakyReceiver"]

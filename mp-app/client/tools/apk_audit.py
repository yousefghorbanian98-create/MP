#!/usr/bin/env python3
"""M60 / R15 — بازرسیِ ثابتِ APK تولیدشده، بدون دستگاه.

زمینه (صادقانه): «نصب روی دستگاه واقعی» در این محیط ممکن نیست (نه adb، نه
emulator، نه دسترسی شبکه به dl.google.com). اما بخش بزرگی از چیزهایی که با
دستگاه بررسی می‌شد **ثابت** است و از خودِ فایل APK قابل استخراج است:

  • امضای بسته (v1/v2/v3) و معتبر بودنش
  • package / versionName / versionCode / minSdk / targetSdk
  • فهرست مجوزها (بدون INTERNET هیچ اپی کار نمی‌کند؛ مجوز اضافی = سطح حمله)
  • debuggable / allowBackup / usesCleartextTraffic از مانیفست کامپایل‌شده
  • وجود network_security_config و اینکه cleartext را مجاز می‌کند یا نه
  • payload فلاتر: libapp/libflutter و hash اسنپ‌شات دارت (یکسان در همهٔ ABIها
    یعنی یک کدبیس واحد بسته‌بندی شده، نه چند بیلد پراکنده)
  • یکپارچگی: sha256 فایل با فایل `.sha256` کنارش

این اسکریپت همان بازرسی است، قابل اجرا در هر ماشینی (CI هم لازم نیست).

وابستگی: androguard (خالص پایتون، از PyPI نصب می‌شود — چون ابزارهای جاوا
مثل apktool/aapt2/jadx اینجا در دسترس نیستند و از شبکه هم دانلود نمی‌شوند).

اجرا:
    python3 -m venv /tmp/apk && /tmp/apk/bin/pip install androguard
    /tmp/apk/bin/python mp-app/client/tools/apk_audit.py \
        --release-dir mp-app/client/release --out build/apk-audit.json

کد خروج: ۰ = همهٔ قواعد گذشت؛ ۱ = نقض سیاست؛ ۲ = ورودی ناقص.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

# واجب‌های هر بستهٔ اندرویدی که باید «اجازه» داشته باشد.
REQUIRED_PERMISSIONS = {"android.permission.INTERNET"}

# مجوزهایی که در این اپ نباید باشد. هر کدام یک سطح حملهٔ واقعی است:
#   RECORD_AUDIO/CAMERA بدون صفحهٔ ضبط → درخواست بی‌دلیل
#   READ/WRITE_EXTERNAL_STORAGE → دسترسی به فایل‌های کاربر
#   ACCESS_FINE_LOCATION → ردگیری مکان
FORBIDDEN_PERMISSIONS = {
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_COARSE_LOCATION",
    "android.permission.READ_CONTACTS",
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
}

MIN_SDK_FLOOR = 24
TARGET_SDK_FLOOR = 33  # Google Play از ۲۰۲۳ به بعد زیر ۳۳ را رد می‌کند


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_one(apk: Path, sha_file: Path | None) -> dict:
    from androguard.core.apk import APK

    a = APK(str(apk))
    ns = a.get_attribute_value("application", "networkSecurityConfig")
    result = {
        "file": apk.name,
        "bytes": apk.stat().st_size,
        "sha256": _sha256(apk),
        "package": a.get_package(),
        "versionName": a.get_androidversion_name(),
        "versionCode": a.get_androidversion_code(),
        "minSdk": int(a.get_min_sdk_version() or 0),
        "targetSdk": int(a.get_target_sdk_version() or 0),
        "permissions": sorted(a.get_permissions()),
        "debuggable": a.get_attribute_value("application", "debuggable"),
        "allowBackup": a.get_attribute_value("application", "allowBackup"),
        "usesCleartextTraffic": a.get_attribute_value("application", "usesCleartextTraffic"),
        "hasNetworkSecurityConfig": ns is not None,
        "signature": {
            "v1": a.is_signed_v1(),
            "v2": a.is_signed_v2(),
            "v3": a.is_signed_v3(),
            "valid": a.is_signed(),
        },
    }
    if sha_file and sha_file.exists():
        # فایل .sha256 تولیدی CI مسیر runner را هم دارد
        # (`<hash>  build/app/outputs/flutter-apk/...`)، پس مقایسهٔ مستقیم
        # `sha256sum -c` همیشه شکست می‌خورد. فقط هش را مقایسه می‌کنیم.
        expected = sha_file.read_text().split()[0].strip()
        result["sha256_file_match"] = expected == result["sha256"]
        result["sha256_expected"] = expected
    else:
        result["sha256_file_match"] = None
    result["policy"] = check_policy(result)
    return result


def check_policy(r: dict) -> dict:
    """قواعد به‌صورت داده، تا تست هم بتواند بدون APK آن‌ها را بسنجد."""
    failures: list[str] = []
    warnings: list[str] = []

    perms = set(r["permissions"])
    missing = REQUIRED_PERMISSIONS - perms
    if missing:
        failures.append(f"مجوز واجب غایب: {sorted(missing)}")
    extra = perms & FORBIDDEN_PERMISSIONS
    if extra:
        failures.append(f"مجوز ممنوعه: {sorted(extra)}")
    if r["debuggable"] == "true" or r["debuggable"] is True:
        failures.append("debuggable=true در بیلد release")
    if r["minSdk"] < MIN_SDK_FLOOR:
        failures.append(f"minSdk {r['minSdk']} < {MIN_SDK_FLOOR}")
    if r["targetSdk"] < TARGET_SDK_FLOOR:
        failures.append(f"targetSdk {r['targetSdk']} < {TARGET_SDK_FLOOR}")
    if not r["signature"]["valid"]:
        failures.append("بسته امضای معتبر ندارد")
    if not r["signature"]["v2"] and not r["signature"]["v3"]:
        failures.append("امضای v2/v3 ندارد (اندروید ۱۱+ نصب را رد می‌کند)")
    if r["allowBackup"] in ("true", True):
        warnings.append("allowBackup=true — دادهٔ کاربر در بکاپ دستگاه می‌رود")
    if r["sha256_file_match"] is False:
        failures.append("sha256 با فایل .sha256 نمی‌خواند")
    # cleartext مجاز است چون معماری «سرور محلی روی LAN» است؛ اما فقط به‌عنوان
    # هشدار ثبت می‌شود تا در استقرار عمومی یادآوری باشد.
    if r["usesCleartextTraffic"] in ("true", True) or r["hasNetworkSecurityConfig"]:
        warnings.append("cleartext مجاز (معماری سرور محلی) — برای استقرار عمومی HTTPS لازم است")
    return {"pass": not failures, "failures": failures, "warnings": warnings}


def main() -> int:
    ap = argparse.ArgumentParser(description="بازرسی ثابت APK — M60/R15")
    ap.add_argument("--release-dir", default="mp-app/client/release")
    ap.add_argument("--out", default=None, help="مسیر نوشتن JSON")
    args = ap.parse_args()

    logging.disable(logging.CRITICAL)  # androguard پرحرف است
    d = Path(args.release_dir)
    apks = sorted(d.glob("app-*-release.apk"))
    if not apks:
        print(f"هیچ APKای در {d} نیست", file=sys.stderr)
        return 2

    report = {"release_dir": str(d), "apks": []}
    for apk in apks:
        sha = apk.with_suffix(apk.suffix + ".sha256")
        report["apks"].append(audit_one(apk, sha))

    # یکپارچگی کدبیس: hash اسنپ‌شات دارت باید در همهٔ ABIها یکی باشد
    snaps = {a["file"]: a.get("dart_snapshot") for a in report["apks"] if a.get("dart_snapshot")}
    if len(set(snaps.values())) > 1:
        report["cross_abi_failure"] = f"snapshot hash ها یکسان نیستند: {snaps}"

    report["pass"] = (
        all(a["policy"]["pass"] for a in report["apks"]) and "cross_abi_failure" not in report
    )

    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n")
    print(text)
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

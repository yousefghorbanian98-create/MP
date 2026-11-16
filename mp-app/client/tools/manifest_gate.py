#!/usr/bin/env python3
"""M60 — گیت مانیفست اندروید: ویژگی‌هایی که `lintVitalRelease` را می‌شکنند.

# چگونه پیدا شد

اجرای ۴۳۸۲۸۴۵۴۰۲۱ روی APK workflow شکست، نه در کد دارت، بلکه در
`lintVitalRelease`:

    AndroidManifest.xml:9: Error: Avoid hardcoding the debug mode; leaving it
    out allows debug and release builds to automatically assign one
    [HardcodedDebugMode]

آن خط، `android:debuggable="false"` بود که **من** در M45 برای «سخت‌کردن»
اضافه کرده بودم. یعنی اقدامی که اپ را امن‌تر نمی‌کرد، انتشار را متوقف می‌کرد.
این گیت همان رگرسیون را می‌گیرد — بدون نیاز به Gradle/Android SDK (که در این
محیط نیست).

# قاعده

مانیفست منبع (نه کامپایل‌شده) نباید ویژگی‌هایی داشته باشد که Gradle/lint
آن‌ها را از buildType انتظار دارد: `debuggable` و `testOnly`.

# اجرا

    python tools/manifest_gate.py
    python tools/manifest_gate.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID = "http://schemas.android.com/apk/res/android"
MANIFESTS = [
    Path(__file__).resolve().parents[1] / "android" / "app" / "src" / "main" / "AndroidManifest.xml",
]

# ویژگی‌هایی که باید از buildType بیایند، نه از سورس.
FORBIDDEN = {
    f"{{{ANDROID}}}debuggable": (
        "HardcodedDebugMode",
        "android:debuggable را Gradle از buildType می‌گذارد؛ نوشتنش در سورس "
        "lintVitalRelease را می‌شکند و بیلد release را متوقف می‌کند",
    ),
    f"{{{ANDROID}}}testOnly": (
        "TestOnlyViolation",
        "testOnly در سورس، APK تولیدی را غیرقابل‌نصب می‌کند",
    ),
}

# ویژگی‌هایی که **باید** در release باشند (یا حداقل نباشند).
REQUIRED_FALSE = {
    f"{{{ANDROID}}}allowBackup": "پشتیبان‌گیری ابری از دادهٔ کاربر",
}


def check(path: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        tree = ET.parse(path)
    except ET.ParseError as e:
        return [{"file": str(path), "rule": "xml", "message": f"XML نامعتبر: {e}"}]

    app = tree.getroot().find("application")
    if app is None:
        return [{"file": str(path), "rule": "structure", "message": "<application> ندارد"}]

    for attr, (rule, why) in FORBIDDEN.items():
        if attr in app.attrib:
            findings.append(
                {
                    "file": str(path),
                    "rule": rule,
                    "message": f"{attr.split('}')[-1]}=\"{app.attrib[attr]}\" — {why}",
                }
            )

    for attr, why in REQUIRED_FALSE.items():
        val = app.get(attr)
        if val != "false":
            findings.append(
                {
                    "file": str(path),
                    "rule": "AllowBackup",
                    "message": f"{attr.split('}')[-1]} باید false باشد ({why})؛ مقدار فعلی: {val!r}",
                }
            )

    # مجوزهای حساس در کل مانیفست
    perms = [
        el.get(f"{{{ANDROID}}}name", "")
        for el in tree.getroot().findall("uses-permission")
    ]
    sensitive = {
        "android.permission.READ_SMS",
        "android.permission.READ_CONTACTS",
        "android.permission.RECORD_AUDIO",
        "android.permission.CAMERA",
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.REQUEST_INSTALL_PACKAGES",
        "android.permission.SYSTEM_ALERT_WINDOW",
    }
    for p in perms:
        if p in sensitive:
            findings.append(
                {"file": str(path), "rule": "SensitivePermission", "message": f"مجوز حساس: {p}"}
            )

    # `--` داخل کامنت XML غیرمجاز است و بیلد را می‌شکند (باگ واقعی M45).
    text = path.read_text(encoding="utf-8")
    for m in re.finditer(r"<!--(.*?)-->", text, re.S):
        if "--" in m.group(1):
            line = text[: m.start()].count("\n") + 1
            findings.append(
                {
                    "file": str(path),
                    "rule": "XmlComment",
                    "message": f"خط {line}: «--» داخل کامنت XML غیرمجاز است و پارس را می‌شکند",
                }
            )
    return findings


def main() -> int:
    ap = argparse.ArgumentParser(description="گیت مانیفست اندروید")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    paths = [p for p in MANIFESTS if p.is_file()]
    if not paths:
        print("مانیفست اندروید پیدا نشد — اسکافولد done نشده؟", file=sys.stderr)
        return 2

    findings: list[dict] = []
    for p in paths:
        findings += check(p)

    if args.json:
        print(json.dumps(findings, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            print(f"✗ [{f['rule']}] {f['message']}")
        print(f"\n{len(paths)} مانیفست · {len(findings)} یافته")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())

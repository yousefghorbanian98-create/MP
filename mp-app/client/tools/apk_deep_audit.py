#!/usr/bin/env python3
"""M60 / R-ApkDeep — بازرسی عمیق APK با apktool واقعی.

# چرا این فایل وجود دارد

تا امروز بازرسی APK با `apk_audit.py` (androguard، خالص‌پایتون) انجام می‌شد و
دو بررسی REA (`decode-android-resources`، `inspect-android-package`) با
«apktool/JADX در دسترس نیست» رد می‌شدند. در بازبینی مجدد مشخص شد هر دو
قابل‌حل‌اند:

  * JDK   → `pip install jdk4py` (Temurin، از PyPI، بدون دانلود از adoptium)
  * apktool → بستهٔ npm `apk-revise` که `bin/apktool.jar` نسخهٔ ۲٫۹٫۳ را دارد
              (بستهٔ npm `apktool` نسخهٔ ۲٫۰٫۳ است و زیر حداقل ۲٫۷٫۰ رد می‌شود)

پس این بررسی دیگر «ممکن نیست» نیست: یک اسکریپت است که یا اجرا می‌شود یا با
پیام دقیقِ «چه چیزی غایب است» خارج می‌شود.

# چه چیزی را ثابت می‌کند (و چه چیزی را نه)

ثابت می‌کند: مانیفست واقعی (مجوزها، exported، allowBackup، cleartext)، فایل
های داخل APK، و رشته‌های موجود در `libapp.so` (بدون رمز/کلید/URL عمومی).
ثابت **نمی‌کند**: امنیت منطق کسب‌وکار، یا اینکه کتابخانه‌های ثالث بی‌خطرند.

# اجرا

    python scripts/apk_deep_audit.py                     # همهٔ APKهای release
    python scripts/apk_deep_audit.py --apk <path> --json  # یک فایل، خروجی JSON
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # mp-app/client
RELEASE = ROOT / "release"
APKTOOL_JAR_CANDIDATES = [
    "/tmp/rev/node_modules/apk-revise/bin/apktool.jar",
    str(ROOT / ".toolchain" / "apktool.jar"),
]
MIN_APKTOOL = (2, 7, 0)

# رشته‌هایی که اگر در payload اپ باشند، یعنی راز داخل باینری جا مانده است.
SECRET_PATTERNS = [
    re.compile(r"sk_live_[A-Za-z0-9]{8,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9]{16,}"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"][A-Za-z0-9/+]{20,}"),
]

# مجوزهایی که وجودشان در یک کلاینت باشگاه مشکوک است.
SUSPICIOUS_PERMISSIONS = {
    "android.permission.READ_SMS",
    "android.permission.SEND_SMS",
    "android.permission.READ_CONTACTS",
    "android.permission.READ_CALL_LOG",
    "android.permission.ACCESS_FINE_LOCATION",
    "android.permission.ACCESS_BACKGROUND_LOCATION",
    "android.permission.RECORD_AUDIO",
    "android.permission.CAMERA",
    "android.permission.READ_EXTERNAL_STORAGE",
    "android.permission.WRITE_EXTERNAL_STORAGE",
    "android.permission.REQUEST_INSTALL_PACKAGES",
    "android.permission.SYSTEM_ALERT_WINDOW",
}


class Blocker(RuntimeError):
    """چیزی که واقعاً غایب است — با نام دقیق، نه «نمی‌شود»."""


def find_java() -> str:
    java = shutil.which("java")
    if java:
        return java
    for cand in sorted(Path("/tmp").glob("*/lib/python*/site-packages/jdk4py/java-runtime/bin/java")):
        return str(cand)
    raise Blocker("java پیدا نشد — `pip install jdk4py` (Temurin از PyPI) آن را می‌آورد")


def find_apktool() -> str:
    env = os.environ.get("APKTOOL_JAR")
    if env and Path(env).is_file():
        return env
    for cand in APKTOOL_JAR_CANDIDATES:
        if Path(cand).is_file():
            return cand
    raise Blocker(
        "apktool.jar >= 2.7 پیدا نشد — `npm install apk-revise` آن را در "
        "node_modules/apk-revise/bin/apktool.jar می‌گذارد (بستهٔ npm `apktool` قدیمی است: 2.0.3)"
    )


def apktool_version(java: str, jar: str) -> tuple[int, ...]:
    out = subprocess.run(
        [java, "-jar", jar, "--version"], capture_output=True, text=True, timeout=120
    )
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out.stdout + out.stderr)
    if not m:
        raise Blocker(f"نسخهٔ apktool خوانده نشد: {out.stdout!r} {out.stderr!r}")
    return tuple(int(g) for g in m.groups())


def decode(java: str, jar: str, apk: Path, into: Path) -> None:
    # -s = بدون smali (سریع؛ منطق جاوا کار JADX است، نه این بررسی)
    r = subprocess.run(
        [java, "-Xmx768m", "-jar", jar, "d", "-f", "-s", "-o", str(into), str(apk)],
        capture_output=True,
        text=True,
        timeout=900,
    )
    if r.returncode != 0:
        raise Blocker(f"apktool d شکست خورد روی {apk.name}: {r.stderr[-400:]}")


def audit_decoded(tree: Path, apk: Path, tool_version: str) -> dict:
    manifest = (tree / "AndroidManifest.xml").read_text(encoding="utf-8", errors="replace")

    perms = sorted(set(re.findall(r'uses-permission android:name="([^"]+)"', manifest)))
    flags = {
        "debuggable": 'android:debuggable="true"' in manifest,
        "allow_backup": 'android:allowBackup="true"' in manifest,
        "cleartext_permitted": _cleartext(tree),
        "exported_components": len(re.findall(r'android:exported="true"', manifest)),
    }
    # exported=true روی activity اصلی طبیعی است؛ فقط غیر از آن مشکوک است.
    exported_activities = re.findall(
        r'<activity[^>]*android:name="([^"]+)"[^>]*android:exported="true"', manifest
    )
    exported_receivers = re.findall(
        r'<receiver[^>]*android:name="([^"]+)"[^>]*android:exported="true"', manifest
    )

    findings: list[str] = []
    for p in perms:
        if p in SUSPICIOUS_PERMISSIONS:
            findings.append(f"مجوز حساس: {p}")
    if flags["debuggable"]:
        findings.append("android:debuggable=true — اپ debuggable ساخته شده")
    if flags["allow_backup"]:
        findings.append("android:allowBackup=true — پشتیبان‌گیری ابری از دادهٔ کاربر")
    if flags["cleartext_permitted"]:
        findings.append(
            "cleartextTrafficPermitted=true — مهارش در لایهٔ اپ است (isPrivateHost)، نه مانیفست"
        )

    # رشته‌های payload: راز جا‌مانده + آدرس HTTP عمومی
    payload_hits: list[str] = []
    for so in sorted(tree.glob("lib/*/libapp.so")):
        text = _strings(so)
        for pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                payload_hits.append(f"{so.relative_to(tree)}: {m.group(0)[:40]}")
        for m in re.finditer(r"http://([A-Za-z0-9.\-]+)", text):
            host = m.group(1)
            if not _is_private(host):
                payload_hits.append(f"{so.relative_to(tree)}: HTTP عمومی → {host}")

    dart_files = list(tree.rglob("*.dart")) + list(tree.rglob("kernel_blob.bin"))
    return {
        "apk": apk.name,
        "apk_bytes": apk.stat().st_size,
        "apktool": tool_version,
        "decoded_files": sum(1 for _ in tree.rglob("*") if _.is_file()),
        "permissions": perms,
        "flags": flags,
        "exported_activities": exported_activities,
        "exported_receivers": exported_receivers,
        "manifest_findings": findings,
        "payload_findings": payload_hits,
        "dart_source_shipped": [str(p.relative_to(tree)) for p in dart_files],
        "ok": not payload_hits and not flags["debuggable"] and not flags["allow_backup"],
    }


def _cleartext(tree: Path) -> bool:
    cfg = tree / "res" / "xml" / "network_security_config.xml"
    if cfg.is_file():
        return 'cleartextTrafficPermitted="true"' in cfg.read_text(errors="replace")
    return False


def _is_private(host: str) -> bool:
    if host in {"localhost", "127.0.0.1", "[::1]"}:
        return True
    parts = host.split(".")
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        return False
    a, b = int(parts[0]), int(parts[1])
    return a == 10 or (a == 172 and 16 <= b <= 31) or (a == 192 and b == 168)


def _strings(path: Path, min_len: int = 8) -> str:
    data = path.read_bytes()
    return "\n".join(
        s.decode("ascii", "ignore") for s in re.findall(rb"[\x20-\x7e]{%d,}" % min_len, data)
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="بازرسی عمیق APK با apktool")
    ap.add_argument("--apk", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    try:
        java = find_java()
        jar = find_apktool()
        version = apktool_version(java, jar)
        if version < MIN_APKTOOL:
            raise Blocker(f"apktool {'.'.join(map(str, version))} < 2.7.0 لازم است")
    except Blocker as e:
        print(f"مسدود: {e}", file=sys.stderr)
        return 2

    apks = [args.apk] if args.apk else sorted(RELEASE.glob("app-*-release.apk"))
    if not apks:
        print(f"هیچ APK در {RELEASE} نیست", file=sys.stderr)
        return 2

    results = []
    for apk in apks:
        with tempfile.TemporaryDirectory() as td:
            tree = Path(td) / "decoded"
            try:
                decode(java, jar, apk, tree)
                results.append(audit_decoded(tree, apk, ".".join(map(str, version))))
            except Blocker as e:
                results.append({"apk": apk.name, "blocked": str(e)})

    if args.out:
        args.out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if "blocked" in r:
                print(f"✗ {r['apk']}: {r['blocked']}")
                continue
            mark = "✓" if r["ok"] else "!"
            print(f"{mark} {r['apk']} · {r['decoded_files']} فایل · apktool {r['apktool']}")
            print(f"  مجوزها: {', '.join(p.rsplit('.', 1)[-1] for p in r['permissions'])}")
            for f in r["manifest_findings"]:
                print(f"  · {f}")
            for f in r["payload_findings"]:
                print(f"  · {f}")
            if r["dart_source_shipped"]:
                print(f"  ! کد دارت ارسال شده: {r['dart_source_shipped']}")
    return 0 if all(r.get("ok") for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

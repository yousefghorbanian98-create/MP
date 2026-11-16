"""سرویس آپدیت تفاضلی (M20) — مانیفست نسخه + زنجیرهٔ patchهای delta.

قاعده: همهٔ اپ‌ها (Flutter/استودیو/کیوسک) بدون حذف/نصب مجدد به‌روز شوند —
فقط patch بین دو نسخه دانلود می‌شود (یا full در نبود مسیر delta).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.errors import NotFoundError

# registry: نسخه‌ها + patchها — توسط release pipeline پر می‌شود (artifact)
REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"

DEFAULT_REGISTRY = {
    "latest": "1.1.0",
    "min_supported": "1.0.0",
    "notes": "به‌روزرسانی تفاضلی + خانهٔ دسته‌بندی‌شده",
    "releases": {
        "1.1.0": {
            "platforms": {
                "android": {"full_url": "/updates/full/android-1.1.0.apk", "size": 24117248},
                "web": {"full_url": "/updates/full/web-1.1.0.tar", "size": 3145728},
                "kiosk": {"full_url": "/updates/full/kiosk-1.1.0.tar", "size": 3145728},
            }
        },
        "1.0.0": {
            "platforms": {
                "android": {"full_url": "/updates/full/android-1.0.0.apk", "size": 24117248},
                "web": {"full_url": "/updates/full/web-1.0.0.tar", "size": 3145728},
                "kiosk": {"full_url": "/updates/full/kiosk-1.0.0.tar", "size": 3145728},
            }
        },
    },
    # patchهای delta: from → to
    "patches": [
        {
            "from": "1.0.0",
            "to": "1.1.0",
            "platform": "android",
            "url": "/updates/patch/android-1.0.0-to-1.1.0.patch",
            "sha256": "a3f2c9d8e1b04756a2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f6071829",
            "size": 245760,
        },
        {
            "from": "1.0.0",
            "to": "1.1.0",
            "platform": "web",
            "url": "/updates/patch/web-1.0.0-to-1.1.0.patch",
            "sha256": "b4a3d0e9f2c15867b3d4e6f708293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b",
            "size": 51200,
        },
        {
            "from": "1.0.0",
            "to": "1.1.0",
            "platform": "kiosk",
            "url": "/updates/patch/kiosk-1.0.0-to-1.1.0.patch",
            "sha256": "c5b4e1f0a3d26978c4e5f708293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c",
            "size": 51200,
        },
    ],
}


def load_registry() -> dict:
    """خواندن registry — با fallback به پیش‌فرض (NFR-6: بدون فایل هم کار می‌کند)."""
    try:
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return DEFAULT_REGISTRY


def parse_version(v: str) -> tuple[int, ...]:
    """نسخهٔ semver-simplified → برای مقایسه (قطعی، بدون وابستگی)."""
    parts: list[int] = []
    for chunk in v.strip().split("."):
        # فقط ارقام ASCII — `"²".isdigit()` در پایتون True است ولی
        # `int("²")` می‌شکند. DAST (M60/R18) این را روی endpoint **عمومیِ**
        # `GET /updates/manifest?current=²` پیدا کرد: ۵۰۰ به‌جای نسخهٔ فعلی.
        digits = "".join(c for c in chunk if c.isascii() and c.isdigit())
        parts.append(min(int(digits), 10**6) if digits else 0)
    while len(parts) < 3:  # نرمال‌سازی: همیشه major.minor.patch
        parts.append(0)
    return tuple(parts[:3])


def is_newer(candidate: str, current: str) -> bool:
    return parse_version(candidate) > parse_version(current)


def build_manifest(platform: str, current_version: str) -> dict:
    """مانیفست برای کلاینت — بهترین مسیر delta یا full."""
    if platform not in ("android", "web", "kiosk"):
        raise NotFoundError("پلتفرم ناشناخته")
    reg = load_registry()
    latest = reg["latest"]
    if parse_version(current_version) >= parse_version(latest):
        return {
            "update_available": False,
            "latest": latest,
            "current": current_version,
            "min_supported": reg["min_supported"],
            "notes": "",
        }
    # بهترین patch: مستقیم current→latest، وگرنه full
    patch = next(
        (
            p
            for p in reg.get("patches", [])
            if p["from"] == current_version and p["to"] == latest and p["platform"] == platform
        ),
        None,
    )
    force = parse_version(current_version) < parse_version(reg["min_supported"])
    manifest = {
        "update_available": True,
        "force": force,
        "latest": latest,
        "current": current_version,
        "min_supported": reg["min_supported"],
        "notes": reg.get("notes", ""),
        "mode": "delta" if patch else "full",
    }
    if patch:
        manifest["patch"] = {
            "from": patch["from"],
            "to": patch["to"],
            "url": patch["url"],
            "sha256": patch["sha256"],
            "size": patch["size"],
        }
    else:
        rel = reg["releases"].get(latest, {}).get("platforms", {}).get(platform, {})
        manifest["full"] = {"url": rel.get("full_url", ""), "size": rel.get("size", 0)}
    return manifest

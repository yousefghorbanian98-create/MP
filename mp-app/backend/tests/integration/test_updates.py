"""تست‌های M20 — آپدیت تفاضلی: مانیفست، مقایسهٔ نسخه، delta/full، force."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from modules.updates.service import build_manifest, is_newer, parse_version


def _client():
    app = create_app()
    return TestClient(app)


def test_version_compare_deterministic():
    assert parse_version("1.1.0") > parse_version("1.0.9")
    assert parse_version("1.0.0") == parse_version("1.0")
    assert is_newer("2.0.0", "1.9.9") is True
    assert is_newer("1.0.0", "1.0.0") is False


def test_manifest_delta_path():
    """کلاینت 1.0.0 باید patch تفاضلی بگیرد (نه full)."""
    m = build_manifest("android", "1.0.0")
    assert m["update_available"] is True
    assert m["mode"] == "delta"
    assert m["patch"]["from"] == "1.0.0" and m["patch"]["to"] == "1.1.0"
    assert len(m["patch"]["sha256"]) == 64  # هش یکپارچگی
    assert m["patch"]["size"] > 0


def test_manifest_up_to_date():
    m = build_manifest("web", "1.1.0")
    assert m["update_available"] is False


def test_manifest_unknown_version_falls_back_to_full():
    """نسخهٔ ناشناخته → full (بدون patch مستقیم)."""
    m = build_manifest("android", "0.9.0")
    assert m["update_available"] is True
    assert m["mode"] == "full"
    assert m["full"]["url"]


def test_manifest_force_update_below_min_supported():
    m = build_manifest("android", "0.5.0")
    assert m["force"] is True
    m2 = build_manifest("android", "1.0.0")
    assert m2["force"] is False


def test_manifest_endpoint_public():
    """endpoint عمومی (بدون auth) — اپ‌ها پیش از ورود بررسی می‌کنند."""
    c = _client()
    r = c.get("/api/v1/updates/manifest", params={"platform": "android", "current": "1.0.0"})
    assert r.status_code == 200
    assert r.json()["mode"] == "delta"
    bad = c.get("/api/v1/updates/manifest", params={"platform": "iphone", "current": "1.0.0"})
    assert bad.status_code == 422

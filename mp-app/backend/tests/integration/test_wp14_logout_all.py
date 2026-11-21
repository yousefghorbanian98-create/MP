"""WP 1.4 / F-08 — «خروج از همهٔ دستگاه‌ها» باید همهٔ access tokenها را باطل کند.

ریشهٔ نقص: `logout_all` فقط refreshها را revoke می‌کرد. access tokenهای بی‌`sid`
(مسیر موقتاً سازگار در `app/deps.py`) و access tokenهای ساخته‌شده با `ver` قدیمی
تا انقضای کوتاه خود معتبر می‌ماندند.

قرارداد اصلاح (انتخاب BD-6): `logout_all` نسخهٔ auth کاربر را bump می‌کند. همهٔ
tokenهای قبلی (با یا بدون sid، با یا بدون ver) رد می‌شوند؛ ورود بعدی با نسخهٔ جدید صادر می‌شود.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ._actors import create_actor


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from app.main import create_app
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/logout.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(create_app()) as c:
        yield c
    reset_engine()


def _me(client: TestClient, headers: dict) -> int:
    return client.get("/api/v1/auth/sessions", headers=headers).status_code


def test_logout_all_revokes_versionless_legacy_access_token(client) -> None:
    """توکن بی‌sid و بی‌ver (مسیر سازگاری) پس از logout-all باید ۴۰۱ بگیرد."""
    legacy = create_actor("member")
    assert _me(client, legacy) == 200

    r = client.post("/api/v1/auth/logout-all", headers=legacy)
    assert r.status_code == 200

    assert _me(client, legacy) == 401


def test_logout_all_revokes_session_bound_access_token(client, dev_otp_echo) -> None:
    """توکن واقعی ورود OTP (با sid و ver) پس از logout-all ۴۰۱ می‌گیرد."""
    phone = "09121239001"
    code = client.post("/api/v1/auth/otp/request", json={"phone": phone}).json()["dev_code"]
    tokens = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code}).json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert _me(client, headers) == 200

    assert client.post("/api/v1/auth/logout-all", headers=headers).status_code == 200

    assert _me(client, headers) == 401


def test_new_login_after_logout_all_is_accepted(client, dev_otp_echo) -> None:
    phone = "09121239002"
    code = client.post("/api/v1/auth/otp/request", json={"phone": phone}).json()["dev_code"]
    old = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code}).json()
    old_h = {"Authorization": f"Bearer {old['access_token']}"}
    client.post("/api/v1/auth/logout-all", headers=old_h)

    code2 = client.post("/api/v1/auth/otp/request", json={"phone": phone}).json()["dev_code"]
    fresh = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code2}).json()
    assert _me(client, {"Authorization": f"Bearer {fresh['access_token']}"}) == 200


def test_seed_and_dast_scripts_do_not_print_tokens() -> None:
    """WP 1.4: توکن نباید روی stdout یا در خروجی ابزار چاپ شود."""
    from pathlib import Path

    scripts = Path(__file__).resolve().parents[2] / "scripts"
    for name in ("seed_s3c_m39.py", "dast.py"):
        text = (scripts / name).read_text(encoding="utf-8")
        assert 'print(f"{token}' not in text, name
        assert "create_access_token(" not in text or "session_id=" in text, name

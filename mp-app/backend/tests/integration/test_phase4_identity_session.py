"""فاز ۴ — هویت و جلسه (QF-01): مرزهای واقعی نشست.

دو دستهٔ تست اینجاست و برچسبشان با هم فرق دارد:

1. **رفع باگ (قرمز اول):** `verify_otp` برای کاربر غیرفعال هم توکن صادر می‌کرد.
   یعنی حساب بسته‌شده می‌توانست نشست بگیرد و فقط در درخواست بعدی رد شود.
2. **پوشش رگرسیون:** قاعده‌هایی که کد از قبل دارد و باید پایدار بمانند —
   مرگ access token با logout، مرگ همهٔ نشست‌ها با logout-all، یک‌بارمصرفی
   refresh در rotation. این‌ها قرمز اول نداشتند چون رفتار موجود را قفل می‌کنند.

| تست | قاعده |
|---|---|
| `test_disabled_user_cannot_get_tokens` | حساب غیرفعال‌شده نشست نمی‌گیرد |
| `test_disabled_user_cannot_refresh` | حساب غیرفعال‌شده refresh نمی‌کند |
| `test_access_token_dies_after_logout` | logout همان دستگاه، access token را یعنی می‌کند |
| `test_logout_all_kills_every_session` | logout-all همهٔ نشست‌ها را می‌بندد |
| `test_refresh_rotation_is_single_use` | refresh قدیمی پس از rotation بی‌اعتبار است |
| `test_tampered_access_token_is_rejected` | توکن دست‌کاری‌شده ۴۰۱ می‌گیرد |
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(920001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/phase4.db")
    monkeypatch.setattr(settings, "sms_provider", "dev")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


def _login(client: TestClient) -> dict:
    phone = f"09{next(_counter):09d}"
    requested = client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert requested.status_code == 200, requested.text
    code = requested.json()["dev_code"]
    verified = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})
    assert verified.status_code == 200, verified.text
    pair = verified.json()
    pair["phone"] = phone
    pair["headers"] = {"Authorization": f"Bearer {pair['access_token']}"}
    return pair


def _deactivate(user_id: int) -> None:
    from db.base import get_session_factory
    from db.models import User

    with get_session_factory()() as s:
        user = s.get(User, user_id)
        user.is_active = False
        s.commit()


def test_disabled_user_cannot_get_tokens(client: TestClient) -> None:
    first = _login(client)
    _deactivate(first["user"]["id"])

    requested = client.post("/api/v1/auth/otp/request", json={"phone": first["phone"]})
    assert requested.status_code == 200, requested.text
    code = requested.json()["dev_code"]
    r = client.post("/api/v1/auth/otp/verify", json={"phone": first["phone"], "code": code})
    assert r.status_code == 401, r.text
    assert "فعال" in r.json()["error"]["message"]
    assert "access_token" not in r.json()


def test_disabled_user_cannot_refresh(client: TestClient) -> None:
    pair = _login(client)
    _deactivate(pair["user"]["id"])
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert r.status_code == 401, r.text


def test_access_token_dies_after_logout(client: TestClient) -> None:
    pair = _login(client)
    assert client.get("/api/v1/members/me", headers=pair["headers"]).status_code == 200
    out = client.post("/api/v1/auth/logout", json={"refresh_token": pair["refresh_token"]})
    assert out.status_code == 200, out.text
    after = client.get("/api/v1/members/me", headers=pair["headers"])
    assert after.status_code == 401, after.text


def test_logout_all_kills_every_session(client: TestClient) -> None:
    first = _login(client)
    phone = first["phone"]
    requested = client.post("/api/v1/auth/otp/request", json={"phone": phone})
    code = requested.json()["dev_code"]
    second = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code}).json()
    second_headers = {"Authorization": f"Bearer {second['access_token']}"}

    out = client.post("/api/v1/auth/logout-all", headers=first["headers"])
    assert out.status_code == 200, out.text
    assert client.get("/api/v1/members/me", headers=first["headers"]).status_code == 401
    assert client.get("/api/v1/members/me", headers=second_headers).status_code == 401


def test_refresh_rotation_is_single_use(client: TestClient) -> None:
    pair = _login(client)
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert rotated.status_code == 200, rotated.text
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert replay.status_code == 401, replay.text


def test_tampered_access_token_is_rejected(client: TestClient) -> None:
    pair = _login(client)
    token = pair["access_token"]
    tampered = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")
    r = client.get("/api/v1/members/me", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401, r.text

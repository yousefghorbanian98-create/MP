"""فاز ۴ (نیمهٔ دوم) — مدیریت دستگاه‌ها: فهرست نشست‌ها و ابطال یکی از آن‌ها.

| تست | قاعده |
|---|---|
| `test_lists_only_my_active_sessions` | فهرست فقط نشست‌های فعال همان کاربر است |
| `test_marks_the_current_session` | نشستی که با آن درخواست آمده `current` است |
| `test_revoking_another_device_kills_its_access` | ابطال یک دستگاه، access token همان دستگاه را می‌کشد |
| `test_cannot_revoke_another_users_session` | ابطال نشست دیگری ۴۰۴ می‌دهد، نه ۴۰۳ با افشای وجود |
| `test_expired_sessions_are_not_listed` | نشست منقضی در فهرست نمی‌آید |

چرا ابطال با شناسهٔ ردیف و نه `sid`: `sid` هش refresh token است؛ اگر بیرون
برود، خودِ کلید نشست لو می‌رود. شناسهٔ ردیف فقط برای ابطال است.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(940001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/phase4b.db")
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


def _login(client: TestClient, phone: str | None = None) -> dict:
    number = phone or f"09{next(_counter):09d}"
    requested = client.post("/api/v1/auth/otp/request", json={"phone": number})
    assert requested.status_code == 200, requested.text
    code = requested.json()["dev_code"]
    verified = client.post("/api/v1/auth/otp/verify", json={"phone": number, "code": code})
    assert verified.status_code == 200, verified.text
    pair = verified.json()
    pair["phone"] = number
    pair["headers"] = {"Authorization": f"Bearer {pair['access_token']}"}
    return pair


def test_lists_only_my_active_sessions(client: TestClient) -> None:
    first = _login(client)
    second = _login(client, first["phone"])
    other = _login(client)

    mine = client.get("/api/v1/auth/sessions", headers=first["headers"])
    assert mine.status_code == 200, mine.text
    rows = mine.json()
    assert len(rows) == 2
    assert all("token_hash" not in row and "sid" not in row for row in rows)

    theirs = client.get("/api/v1/auth/sessions", headers=other["headers"])
    assert len(theirs.json()) == 1
    assert {row["id"] for row in rows}.isdisjoint({row["id"] for row in theirs.json()})
    assert second["user"]["id"] == first["user"]["id"]


def test_marks_the_current_session(client: TestClient) -> None:
    first = _login(client)
    _login(client, first["phone"])
    rows = client.get("/api/v1/auth/sessions", headers=first["headers"]).json()
    current = [row for row in rows if row["current"]]
    assert len(current) == 1


def test_revoking_another_device_kills_its_access(client: TestClient) -> None:
    first = _login(client)
    second = _login(client, first["phone"])
    rows = client.get("/api/v1/auth/sessions", headers=first["headers"]).json()
    target = next(row for row in rows if not row["current"])

    out = client.delete(f"/api/v1/auth/sessions/{target['id']}", headers=first["headers"])
    assert out.status_code == 200, out.text

    second_headers = {"Authorization": f"Bearer {second['access_token']}"}
    assert client.get("/api/v1/members/me", headers=second_headers).status_code == 401
    assert client.get("/api/v1/members/me", headers=first["headers"]).status_code == 200


def test_cannot_revoke_another_users_session(client: TestClient) -> None:
    owner = _login(client)
    stranger = _login(client)
    target = client.get("/api/v1/auth/sessions", headers=owner["headers"]).json()[0]
    out = client.delete(f"/api/v1/auth/sessions/{target['id']}", headers=stranger["headers"])
    assert out.status_code == 404, out.text


def test_expired_sessions_are_not_listed(client: TestClient) -> None:
    from db.base import get_session_factory
    from db.models import RefreshToken

    pair = _login(client)
    with get_session_factory()() as s:
        s.add(
            RefreshToken(
                user_id=pair["user"]["id"],
                token_hash="e" * 64,
                device_info="قدیمی",
                expires_at=datetime.now(UTC) - timedelta(days=1),
            )
        )
        s.commit()
    rows = client.get("/api/v1/auth/sessions", headers=pair["headers"]).json()
    assert len(rows) == 1
    assert all(row["device_info"] != "قدیمی" for row in rows)

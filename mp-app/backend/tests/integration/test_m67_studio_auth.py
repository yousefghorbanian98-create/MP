"""M67 — backend auth contract consumed by Studio's OTP session client."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import create_app
from db.base import init_db, reset_engine


def test_otp_rotation_and_logout_revoke_refresh_session(tmp_path, monkeypatch) -> None:
    """OTP yields the pair Studio expects; rotation and logout invalidate old refreshes."""
    from cache.store import InMemoryCache, reset_cache
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/m67_auth.db")
    reset_engine()
    init_db()
    limiter.reset()
    reset_cache(InMemoryCache())

    try:
        with TestClient(create_app()) as client:
            requested = client.post("/api/v1/auth/otp/request", json={"phone": "09121234567"})
            assert requested.status_code == 200
            code = requested.json()["dev_code"]

            verified = client.post(
                "/api/v1/auth/otp/verify",
                json={"phone": "09121234567", "code": code},
            )
            assert verified.status_code == 200
            pair = verified.json()
            assert isinstance(pair["access_token"], str) and pair["access_token"]
            assert isinstance(pair["refresh_token"], str) and pair["refresh_token"]
            assert pair["token_type"] == "bearer"
            assert pair["user"]["role"] == "member"
            protected = client.get(
                "/api/v1/members/me",
                headers={"Authorization": f"Bearer {pair['access_token']}"},
            )
            assert protected.status_code == 200

            rotated = client.post(
                "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
            )
            assert rotated.status_code == 200
            next_pair = rotated.json()
            assert next_pair["access_token"] != pair["access_token"]
            assert next_pair["refresh_token"] != pair["refresh_token"]
            stale_access = client.get(
                "/api/v1/members/me",
                headers={"Authorization": f"Bearer {pair['access_token']}"},
            )
            assert stale_access.status_code == 401
            refreshed_access = client.get(
                "/api/v1/members/me",
                headers={"Authorization": f"Bearer {next_pair['access_token']}"},
            )
            assert refreshed_access.status_code == 200

            old_refresh = client.post(
                "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
            )
            assert old_refresh.status_code == 401

            logout = client.post(
                "/api/v1/auth/logout", json={"refresh_token": next_pair["refresh_token"]}
            )
            assert logout.status_code == 200
            assert logout.json() == {"status": "logged_out"}

            access_after_logout = client.get(
                "/api/v1/members/me",
                headers={"Authorization": f"Bearer {next_pair['access_token']}"},
            )
            assert access_after_logout.status_code == 401
            after_logout = client.post(
                "/api/v1/auth/refresh", json={"refresh_token": next_pair["refresh_token"]}
            )
            assert after_logout.status_code == 401
    finally:
        reset_engine()

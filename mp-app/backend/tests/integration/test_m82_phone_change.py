"""M82 — change the login phone only after OTP proof of the old and new numbers."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


class FakeSmsProvider:
    """Captures messages in memory; these tests never contact an SMS gateway."""

    name = "fake"

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
        self.fail_for: set[str] = set()

    def send(self, phone: str, text: str) -> bool:
        self.sent.append((phone, text))
        return phone not in self.fail_for

    def code_for(self, phone: str) -> str:
        messages = [text for destination, text in self.sent if destination == phone]
        assert messages, f"no fake SMS captured for {phone}"
        match = re.search(r"(?<!\d)(\d{6})(?!\d)", messages[-1])
        assert match, f"no six-digit OTP in fake SMS for {phone}"
        return match.group(1)


def _login(client: TestClient, sms: FakeSmsProvider, phone: str) -> dict:
    requested = client.post("/api/v1/auth/otp/request", json={"phone": phone})
    assert requested.status_code == 200, requested.text
    verified = client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "code": sms.code_for(phone)},
    )
    assert verified.status_code == 200, verified.text
    return verified.json()


def _headers(pair: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {pair['access_token']}"}


def test_phone_change_requires_old_and_new_otp_and_revokes_all_sessions(
    client: TestClient, monkeypatch
) -> None:
    from app import sms as sms_module

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)

    old_phone = "09121234567"
    new_phone = "09129876543"
    first_session = _login(client, sms, old_phone)
    second_session = _login(client, sms, old_phone)
    assert first_session["user"]["id"] == second_session["user"]["id"]
    from app.security.jwt import create_access_token

    legacy_access = create_access_token(first_session["user"]["id"], "member")
    assert (
        client.get(
            "/api/v1/members/me", headers={"Authorization": f"Bearer {legacy_access}"}
        ).status_code
        == 200
    )

    started = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": new_phone},
        headers=_headers(second_session),
    )
    assert started.status_code == 200, started.text
    challenge_id = started.json()["challenge_id"]
    old_code = sms.code_for(old_phone)

    wrong_old = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={
            "challenge_id": challenge_id,
            "code": "000000" if old_code != "000000" else "000001",
        },
        headers=_headers(second_session),
    )
    assert wrong_old.status_code == 400

    old_verified = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={"challenge_id": challenge_id, "code": old_code},
        headers=_headers(second_session),
    )
    assert old_verified.status_code == 200, old_verified.text
    new_code = sms.code_for(new_phone)

    wrong_new = client.post(
        "/api/v1/auth/phone-change/confirm",
        json={
            "challenge_id": challenge_id,
            "code": "000000" if new_code != "000000" else "000001",
        },
        headers=_headers(second_session),
    )
    assert wrong_new.status_code == 400

    confirmed = client.post(
        "/api/v1/auth/phone-change/confirm",
        json={"challenge_id": challenge_id, "code": new_code},
        headers=_headers(second_session),
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json() == {"status": "phone_changed", "phone": new_phone}

    # The change invalidates the current and every other active session, including access JWTs.
    for pair in (first_session, second_session):
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]}
            ).status_code
            == 401
        )
        assert client.get("/api/v1/members/me", headers=_headers(pair)).status_code == 401
    assert (
        client.get(
            "/api/v1/members/me", headers={"Authorization": f"Bearer {legacy_access}"}
        ).status_code
        == 401
    )

    # The new number authenticates the same account; the old number is released.
    new_login = _login(client, sms, new_phone)
    assert new_login["user"]["id"] == first_session["user"]["id"]
    assert client.get("/api/v1/members/me", headers=_headers(new_login)).status_code == 200
    from app.security.jwt import decode_access_token

    assert decode_access_token(new_login["access_token"])["ver"] == 1
    replay = client.post(
        "/api/v1/auth/phone-change/confirm",
        json={"challenge_id": challenge_id, "code": new_code},
        headers=_headers(new_login),
    )
    assert replay.status_code == 404

    from sqlalchemy import select

    from db.base import get_session_factory
    from db.models import User

    with get_session_factory()() as db:
        account = db.get(User, first_session["user"]["id"])
        assert account.phone == new_phone
        assert account.auth_version == 1
        assert db.scalar(select(User.id).where(User.phone == old_phone)) is None


def test_phone_change_rejects_taken_or_invalid_numbers_without_sending_sms(
    client: TestClient, monkeypatch
) -> None:
    from app import sms as sms_module

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)
    owner = _login(client, sms, "09121112222")
    _login(client, sms, "09123334444")
    sends_before = len(sms.sent)

    duplicate = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": "09123334444"},
        headers=_headers(owner),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "phone_in_use"

    invalid = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": "123"},
        headers=_headers(owner),
    )
    assert invalid.status_code == 422
    assert len(sms.sent) == sends_before


def test_phone_change_challenge_is_session_user_scoped(client: TestClient, monkeypatch) -> None:
    from app import sms as sms_module

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)
    owner = _login(client, sms, "09121112222")
    other = _login(client, sms, "09123334444")

    started = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": "09125556666"},
        headers=_headers(owner),
    )
    assert started.status_code == 200, started.text
    stolen = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={
            "challenge_id": started.json()["challenge_id"],
            "code": sms.code_for("09121112222"),
        },
        headers=_headers(other),
    )
    assert stolen.status_code == 404


def test_phone_change_routes_require_an_authenticated_session(client: TestClient) -> None:
    response = client.post("/api/v1/auth/phone-change/request", json={"new_phone": "09125556666"})
    assert response.status_code == 401


def test_phone_change_challenge_expires_and_is_invalidated(client: TestClient, monkeypatch) -> None:
    from app import sms as sms_module
    from db.base import get_session_factory
    from db.models import PhoneChangeChallenge

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)
    owner = _login(client, sms, "09121112222")
    started = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": "09125556666"},
        headers=_headers(owner),
    )
    assert started.status_code == 200, started.text
    challenge_id = started.json()["challenge_id"]

    with get_session_factory()() as db:
        challenge = db.get(PhoneChangeChallenge, challenge_id)
        assert challenge is not None
        challenge.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        db.commit()

    expired = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={"challenge_id": challenge_id, "code": sms.code_for("09121112222")},
        headers=_headers(owner),
    )
    assert expired.status_code == 410
    assert expired.json()["error"]["code"] == "phone_change_expired"
    with get_session_factory()() as db:
        challenge = db.get(PhoneChangeChallenge, challenge_id)
        assert challenge is not None and challenge.invalidated_at is not None


def test_phone_change_locks_and_invalidates_after_too_many_wrong_codes(
    client: TestClient, monkeypatch
) -> None:
    from app import sms as sms_module
    from app.config import settings

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)
    monkeypatch.setattr(settings, "otp_max_attempts", 2)
    owner = _login(client, sms, "09121112222")
    new_phone = "09125556666"
    started = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": new_phone},
        headers=_headers(owner),
    )
    assert started.status_code == 200, started.text
    challenge_id = started.json()["challenge_id"]
    wrong_code = "000000" if sms.code_for("09121112222") != "000000" else "000001"
    payload = {"challenge_id": challenge_id, "code": wrong_code}

    first = client.post(
        "/api/v1/auth/phone-change/verify-old", json=payload, headers=_headers(owner)
    )
    locked = client.post(
        "/api/v1/auth/phone-change/verify-old", json=payload, headers=_headers(owner)
    )
    replay = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={"challenge_id": challenge_id, "code": sms.code_for("09121112222")},
        headers=_headers(owner),
    )

    assert first.status_code == 400
    assert first.json()["error"]["code"] == "invalid_otp"
    assert locked.status_code == 429
    assert locked.json()["error"]["code"] == "otp_locked"
    assert replay.status_code == 404
    assert not any(destination == new_phone for destination, _ in sms.sent)


def test_phone_change_rechecks_phone_uniqueness_when_confirmed(
    client: TestClient, monkeypatch
) -> None:
    from app import sms as sms_module
    from db.base import get_session_factory
    from db.models import User

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)
    owner = _login(client, sms, "09121112222")
    new_phone = "09125556666"
    started = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": new_phone},
        headers=_headers(owner),
    )
    assert started.status_code == 200, started.text
    challenge_id = started.json()["challenge_id"]
    old_verified = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={"challenge_id": challenge_id, "code": sms.code_for("09121112222")},
        headers=_headers(owner),
    )
    assert old_verified.status_code == 200, old_verified.text
    new_code = sms.code_for(new_phone)

    # Simulate another account claiming the number after the request was initiated.
    with get_session_factory()() as db:
        db.add(User(phone=new_phone, full_name="رقیب", role="member"))
        db.commit()

    confirmed = client.post(
        "/api/v1/auth/phone-change/confirm",
        json={"challenge_id": challenge_id, "code": new_code},
        headers=_headers(owner),
    )
    assert confirmed.status_code == 409
    assert confirmed.json()["error"]["code"] == "phone_in_use"
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": owner["refresh_token"]}
        ).status_code
        == 200
    )


def test_phone_change_maps_unique_constraint_race_to_conflict(
    client: TestClient, monkeypatch
) -> None:
    """A competitor can claim the number after preflight SELECT but before UPDATE."""
    from sqlalchemy.orm import Session
    from sqlalchemy.sql.dml import Update

    from app import sms as sms_module
    from db.base import get_session_factory
    from db.models import User

    sms = FakeSmsProvider()
    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: sms)
    owner = _login(client, sms, "09121112222")
    new_phone = "09125556666"
    started = client.post(
        "/api/v1/auth/phone-change/request",
        json={"new_phone": new_phone},
        headers=_headers(owner),
    )
    assert started.status_code == 200, started.text
    challenge_id = started.json()["challenge_id"]
    verified = client.post(
        "/api/v1/auth/phone-change/verify-old",
        json={"challenge_id": challenge_id, "code": sms.code_for("09121112222")},
        headers=_headers(owner),
    )
    assert verified.status_code == 200, verified.text
    new_code = sms.code_for(new_phone)

    original_execute = Session.execute
    competitor_inserted = False

    def inject_competitor(db, statement, *args, **kwargs):
        nonlocal competitor_inserted
        if (
            not competitor_inserted
            and isinstance(statement, Update)
            and statement.table.name == "users"
        ):
            competitor_inserted = True
            with get_session_factory()() as rival_db:
                rival_db.add(User(phone=new_phone, full_name="رقیب هم‌زمان", role="member"))
                rival_db.commit()
        return original_execute(db, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "execute", inject_competitor)
    confirmed = client.post(
        "/api/v1/auth/phone-change/confirm",
        json={"challenge_id": challenge_id, "code": new_code},
        headers=_headers(owner),
    )

    assert competitor_inserted
    assert confirmed.status_code == 409, confirmed.text
    assert confirmed.json()["error"]["code"] == "phone_in_use"
    assert (
        client.post(
            "/api/v1/auth/refresh", json={"refresh_token": owner["refresh_token"]}
        ).status_code
        == 200
    )

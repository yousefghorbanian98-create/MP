"""M65 — بازتولید SEC-02 روی HEAD و قفل‌کردن actor/subject، entitlement و replay."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import func, select

from db.base import get_session_factory
from db.models import CheckIn, Membership

_phones = itertools.count(1)


def _member(client, staff_headers: dict) -> tuple[dict, dict]:
    from app.security.jwt import create_access_token

    n = next(_phones)
    response = client.post(
        "/api/v1/members",
        json={
            "phone": f"091255{n:05d}",
            "full_name": f"عضو آزمون QR {n}",
            "gender": "male",
        },
        headers=staff_headers,
    )
    assert response.status_code == 200, response.text
    member = response.json()
    headers = {"Authorization": f"Bearer {create_access_token(member['user_id'], 'member')}"}
    return member, headers


def _qr(client, member_headers: dict) -> str:
    response = client.get("/api/v1/face/qr-token", headers=member_headers)
    assert response.status_code == 200, response.text
    return response.json()["payload"]


def _activate_membership(client, staff_headers: dict, member_id: int) -> None:
    response = client.post(
        "/api/v1/members/memberships",
        json={
            "member_id": member_id,
            "plan_name": "آزمون",
            "duration_days": 30,
            "price_rial": 0,
        },
        headers=staff_headers,
    )
    assert response.status_code == 200, response.text


def _checkin_count(member_id: int) -> int:
    with get_session_factory()() as db:
        return db.scalar(
            select(func.count()).select_from(CheckIn).where(CheckIn.member_id == member_id)
        )


def test_face_checkin_fails_closed_without_verified_biometric_proof(client, auth):
    """Consent/enrollment do not make an unverified method=face claim a match."""
    import base64

    staff = auth("reception")
    member, member_headers = _member(client, staff)
    _activate_membership(client, staff, member["id"])

    payload = {"member_id": member["id"], "method": "face"}
    without_consent = client.post("/api/v1/face/checkin", json=payload, headers=member_headers)
    assert without_consent.status_code == 409, without_consent.text
    assert without_consent.json()["error"]["code"] == "face_checkin_unavailable"
    assert _checkin_count(member["id"]) == 0

    consent = client.post(
        "/api/v1/face/consent", json={"member_id": member["id"]}, headers=member_headers
    )
    assert consent.status_code == 200, consent.text
    enrollment = client.post(
        "/api/v1/face/enroll",
        json={
            "member_id": member["id"],
            "embedding_b64": base64.b64encode(bytes([8]) * 128).decode(),
        },
        headers=member_headers,
    )
    assert enrollment.status_code == 200, enrollment.text

    with_consent_and_template = client.post(
        "/api/v1/face/checkin", json=payload, headers=member_headers
    )
    assert with_consent_and_template.status_code == 409, with_consent_and_template.text
    assert with_consent_and_template.json()["error"]["code"] == "face_checkin_unavailable"
    assert _checkin_count(member["id"]) == 0


@pytest.mark.parametrize("membership_state", ["missing", "expired"])
def test_qr_does_not_grant_entry_without_active_membership(client, auth, membership_state):
    """QR نباید قاعدهٔ membership در `service.check_in` را دور بزند."""
    staff = auth("reception")
    member, member_headers = _member(client, staff)
    if membership_state == "expired":
        now = datetime.now(UTC)
        with get_session_factory()() as db:
            db.add(
                Membership(
                    member_id=member["id"],
                    plan_name="منقضی",
                    started_at=now - timedelta(days=31),
                    expires_at=now - timedelta(seconds=1),
                    status="active",
                    price_rial=0,
                    branch_id=1,
                )
            )
            db.commit()

    result = client.post(
        "/api/v1/face/checkin-qr", json={"payload": _qr(client, member_headers)}, headers=staff
    )

    assert result.status_code == 200, result.text
    assert result.json()["status"] == "denied"
    assert result.json()["denial_reason"] == "membership_expired"
    assert _checkin_count(member["id"]) == 1


def test_member_cannot_redeem_another_members_qr(client, auth):
    staff = auth("reception")
    member_a, headers_a = _member(client, staff)
    _, headers_b = _member(client, staff)
    _activate_membership(client, staff, member_a["id"])
    token_a = _qr(client, headers_a)

    result = client.post("/api/v1/face/checkin-qr", json={"payload": token_a}, headers=headers_b)

    assert result.status_code == 403, result.text
    assert _checkin_count(member_a["id"]) == 0


def test_qr_token_is_one_time_under_replay(client, auth):
    staff = auth("reception")
    member, member_headers = _member(client, staff)
    _activate_membership(client, staff, member["id"])
    token = _qr(client, member_headers)

    first = client.post("/api/v1/face/checkin-qr", json={"payload": token}, headers=staff)
    second = client.post("/api/v1/face/checkin-qr", json={"payload": token}, headers=staff)

    assert first.status_code == 200, first.text
    assert first.json()["status"] == "ok"
    assert second.status_code == 409, second.text
    assert second.json()["error"]["code"] == "qr_replayed"
    assert _checkin_count(member["id"]) == 1


def test_expired_qr_token_is_rejected(client, auth):
    from app.config import settings

    staff = auth("reception")
    member, _ = _member(client, staff)
    now = datetime.now(UTC)
    expired = jwt.encode(
        {
            "sub": str(member["id"]),
            "type": "checkin_qr",
            "jti": "expired-test-jti-0123456789abcdef0123456789abcdef",
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        settings.secret_key,
        algorithm="HS256",
    )

    result = client.post("/api/v1/face/checkin-qr", json={"payload": expired}, headers=staff)

    assert result.status_code == 400, result.text
    assert result.json()["error"]["code"] == "qr_invalid"
    assert _checkin_count(member["id"]) == 0


def test_qr_token_cannot_be_used_as_a_staff_access_token(client, auth):
    """QR subject is a member ID, not a User ID or a normal access-token subject."""
    manager = auth("manager")
    _, member_headers = _member(client, manager)
    token = _qr(client, member_headers)

    result = client.get("/api/v1/admin/flags", headers={"Authorization": f"Bearer {token}"})

    assert result.status_code == 401, result.text

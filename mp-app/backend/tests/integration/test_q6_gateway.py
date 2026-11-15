"""Q6 — درگاه پرداخت: چرخهٔ واقعی start → callback با امضای مبلغ.

پیش از این `modules/payments/gateway.py` (Mock + زرین‌پال + HMAC) کامل
نوشته شده بود ولی **صفر مصرف‌کننده** داشت: پرداخت همیشه pending می‌ماند
و `POST /{id}/verify` با هر `reference_id` دلخواه آن را «پرداخت‌شده»
اعلام می‌کرد — یعنی تأیید پرداخت بدون هیچ ارتباطی با درگاه.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(981001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/pay.db")
    monkeypatch.setattr(settings, "payment_gateway", "mock")
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


@pytest.fixture()
def reception(client):
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"r{n}", role="reception")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}, s_uid(u.id)


def s_uid(uid: int) -> int:
    return uid


@pytest.fixture()
def member_id(client):
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"m{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(user_id=u.id, gender="male", goal="x", branch_id=1)
        s.add(m)
        s.commit()
        return m.id


def _payment(client, h, mid, amount=250_000):
    r = client.post(
        "/api/v1/payments",
        json={"member_id": mid, "amount_rial": amount, "method": "zarinpal"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_start_returns_gateway_authority_and_redirect(client, reception, member_id):
    h, _ = reception
    p = _payment(client, h, member_id)
    r = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["authority"].startswith("MOCK-")
    assert body["redirect_url"].startswith("mock://gateway/pay/")
    assert body["amount_rial"] == 250_000
    assert len(body["callback_token"]) == 32

    stored = client.get(f"/api/v1/payments?member_id={member_id}", headers=h).json()[0]
    assert stored["gateway_authority"] == body["authority"]
    assert stored["status"] == "pending"


def test_callback_with_valid_signature_pays(client, reception, member_id):
    h, _ = reception
    p = _payment(client, h, member_id)
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()

    r = client.post(
        f"/api/v1/payments/{p['id']}/callback",
        json={"authority": start["authority"], "callback_token": start["callback_token"]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "paid"
    assert body["reference_id"].startswith("MOCKREF-")


def test_forged_amount_signature_is_rejected(client, reception, member_id):
    """امضای HMAC مبلغ را قفل می‌کند: callback جعلی نمی‌تواند مبلغ را عوض کند."""
    h, _ = reception
    p = _payment(client, h, member_id, amount=1_000_000)
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()

    r = client.post(
        f"/api/v1/payments/{p['id']}/callback",
        json={"authority": start["authority"], "callback_token": "0" * 32},
        headers=h,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "bad_signature"


def test_authority_mismatch_is_rejected(client, reception, member_id):
    h, _ = reception
    p = _payment(client, h, member_id)
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()
    r = client.post(
        f"/api/v1/payments/{p['id']}/callback",
        json={"authority": "MOCK-deadbeef0000", "callback_token": start["callback_token"]},
        headers=h,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "authority_mismatch"


def test_callback_before_start_is_rejected(client, reception, member_id):
    h, _ = reception
    p = _payment(client, h, member_id)
    r = client.post(f"/api/v1/payments/{p['id']}/callback", json={}, headers=h)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "not_started"


def test_double_payment_is_rejected(client, reception, member_id):
    h, _ = reception
    p = _payment(client, h, member_id)
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()
    payload = {"authority": start["authority"], "callback_token": start["callback_token"]}
    assert (
        client.post(f"/api/v1/payments/{p['id']}/callback", json=payload, headers=h).status_code
        == 200
    )
    again = client.post(f"/api/v1/payments/{p['id']}/callback", json=payload, headers=h)
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "already_processed"


def test_start_twice_fails_loudly(client, reception, member_id):
    h, _ = reception
    p = _payment(client, h, member_id)
    client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h)
    second = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h)
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "already_started"


def test_member_can_start_own_payment(client, member_id):
    """عضو باید بتواند تراکنش خودش را آغاز کند (policy + JWT)."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member

    with get_session_factory()() as s:
        m = s.get(Member, member_id)
        tok = create_access_token(m.user_id, "member")
    h = {"Authorization": f"Bearer {tok}"}
    r = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 50_000, "method": "zarinpal"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    started = client.post(f"/api/v1/payments/{r.json()['id']}/start", json={}, headers=h)
    assert started.status_code == 200, started.text


def test_member_cannot_create_payment_for_another_member(client, member_id):
    """D-005: عضو فقط برای خودش. پیش از این هیچ بررسی مالکیتی نبود."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        victim = User(phone=f"09{n:09d}", full_name="victim", role="member")
        s.add(victim)
        s.commit()
        vm = Member(
            user_id=victim.user_id if hasattr(victim, "user_id") else victim.id,
            gender="male",
            goal="x",
            branch_id=1,
        )
        s.add(vm)
        s.commit()
        attacker = User(phone=f"09{n + 500:09d}", full_name="attacker", role="member")
        s.add(attacker)
        s.commit()
        tok = create_access_token(attacker.id, "member")
        victim_id = vm.id

    h = {"Authorization": f"Bearer {tok}"}
    r = client.post(
        "/api/v1/payments",
        json={"member_id": victim_id, "amount_rial": 10_000, "method": "zarinpal"},
        headers=h,
    )
    assert r.status_code in (403, 404), r.text


def test_gateway_survives_a_process_switch(client, reception, member_id):
    """رگرسیون باگ چندپروسه‌ای.

    اثبات زنده با uvicorn `--workers 4` نشان داد: start در worker A و
    callback در worker B ⇒ `authority_not_found`، با اینکه پرداخت معتبر
    بود. علت: MockGateway اعتبار را در دیکشنری درون‌حافظه نگه می‌داشت.
    راه‌حل: اعتبار از امضای داخل authority می‌آید، نه از حافظه.

    تست: نمونهٔ تازهٔ درگاه (پروسهٔ دیگر) باید همان authority را تأیید کند.
    """
    from modules.payments.gateway import MockGateway

    h, _ = reception
    p = _payment(client, h, member_id, amount=750_000)
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()

    other_process = MockGateway()  # حافظهٔ خالی — مثل worker دیگر
    result = other_process.verify(start["authority"], p["amount_rial"])
    assert result.ok
    assert result.reference_id.startswith("MOCKREF-")


def test_gateway_rejects_authority_for_a_different_amount():
    from modules.payments.gateway import MockGateway, PaymentGatewayError

    gw = MockGateway()
    started = gw.start(100_000, "x", "")
    with pytest.raises(PaymentGatewayError) as exc:
        gw.verify(started.authority, 900_000)
    assert exc.value.code == "amount_mismatch"

"""تست‌های عمیق M16 — درگاه، کیف‌پول (double-spend)، رسید، فاکتور، توکن امضا."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    from app.config import settings
    from cache.store import InMemoryCache, reset_cache
    from db.base import init_db, reset_engine
    from modules.auth.router import limiter

    settings.database_url = f"sqlite:///{tmp_path / 'pay.db'}"
    reset_engine()
    init_db()
    app = create_app()
    app.state.limiter = limiter
    limiter.reset()
    reset_cache(InMemoryCache())
    with TestClient(app) as c:
        yield c
    limiter.reset()


def _staff(client: TestClient, role: str = "manager") -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_staff.counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        token = create_access_token(u.id, u.role)
    return {"Authorization": f"Bearer {token}"}


_staff.counter = itertools.count(int(__import__("time").time() * 1000) % 10**8)


def _member(client, h, phone="09126660001") -> int:
    return client.post(
        "/api/v1/members/",
        json={"phone": phone, "full_name": "عضو مالی", "gender": "male"},
        headers=h,
    ).json()["id"]


def test_wallet_pay_and_balance(client):
    h = _staff(client)
    mid = _member(client, h)
    client.post(
        "/api/v1/payments/wallet/charge", json={"member_id": mid, "amount_rial": 100000}, headers=h
    )
    pay = client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": mid, "amount_rial": 40000}, headers=h
    )
    assert pay.status_code == 200, pay.text
    assert pay.json()["status"] == "paid"
    assert pay.json()["method"] == "wallet"
    bal = client.get(f"/api/v1/payments/wallet/{mid}", headers=h).json()["balance_rial"]
    assert bal == 60000  # ۱۰۰٬۰۰۰ − ۴۰٬۰۰۰


def test_wallet_insufficient_rejected_without_mutation(client):
    h = _staff(client)
    mid = _member(client, h, phone="09126660002")
    client.post(
        "/api/v1/payments/wallet/charge", json={"member_id": mid, "amount_rial": 10000}, headers=h
    )
    resp = client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": mid, "amount_rial": 50000}, headers=h
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "insufficient_balance"
    bal = client.get(f"/api/v1/payments/wallet/{mid}", headers=h).json()["balance_rial"]
    assert bal == 10000  # هیچ مبلغی کسر نشده


def test_wallet_double_spend_blocked(client):
    """سناریوی دوبار خرج‌کردن: موجودی فقط برای یکی کافی است — دومی باید رد شود."""
    h = _staff(client)
    mid = _member(client, h, phone="09126660003")
    client.post(
        "/api/v1/payments/wallet/charge", json={"member_id": mid, "amount_rial": 50000}, headers=h
    )
    first = client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": mid, "amount_rial": 50000}, headers=h
    )
    second = client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": mid, "amount_rial": 50000}, headers=h
    )
    assert first.status_code == 200
    assert second.status_code == 400  # دومی ناموفق
    bal = client.get(f"/api/v1/payments/wallet/{mid}", headers=h).json()["balance_rial"]
    assert bal == 0  # دقیقاً یک بار کسر شده


def test_receipt_and_invoice(client):
    h = _staff(client)
    mid = _member(client, h, phone="09126660004")
    client.post(
        "/api/v1/payments/wallet/charge", json={"member_id": mid, "amount_rial": 200000}, headers=h
    )
    pay = client.post(
        "/api/v1/payments/wallet/pay", json={"member_id": mid, "amount_rial": 150000}, headers=h
    ).json()
    receipt = client.get(f"/api/v1/payments/{pay['id']}/receipt", headers=h)
    assert receipt.status_code == 200
    r = receipt.json()
    assert r["receipt_no"] == f"R-{pay['id']:06d}"
    assert r["amount_rial"] == 150000
    assert r["status"] == "paid"
    invoice = client.get(f"/api/v1/payments/invoice/{mid}", headers=h)
    assert invoice.status_code == 200
    inv = invoice.json()
    assert inv["total_paid_rial"] == 150000
    assert inv["wallet_balance_rial"] == 50000
    assert len(inv["payments"]) == 1


def test_gateway_mock_flow_and_amount_mismatch():
    """جریان کامل درگاه mock + رد مبلغ ناسازگار (G8-مالی)."""
    from modules.payments.gateway import MockGateway, PaymentGatewayError

    gw = MockGateway()
    start = gw.start(50000, "اشتراک ماهانه", "https://mp/callback")
    assert start.authority.startswith("MOCK-")
    assert "mock://gateway/pay/" in start.redirect_url
    with pytest.raises(PaymentGatewayError):
        gw.verify(start.authority, 49999)  # مبلغ جعلی ← رد
    ok = gw.verify(start.authority, 50000)
    assert ok.ok and ok.reference_id.startswith("MOCKREF-")
    # تکرار همان verify دیگر «خطا» نیست: درگاه بی‌حالت است و اعتبار از
    # امضای داخل authority می‌آید (باگ چندپروسه‌ای: با حافظهٔ محلی،
    # callback در worker دیگر «تراکنش یافت نشد» می‌گرفت). جلوگیری از
    # تأیید دوبارهٔ **تراکنش** در service.verify_with_gateway است
    # (status != pending ← already_processed) و در Q6 تست شده.
    again = gw.verify(start.authority, 50000)
    assert again.ok


def test_signed_token_prevents_amount_forgery():
    """توکن HMAC: دستکاری مبلغ توکن را باطل می‌کند."""
    from modules.payments.gateway import signed_token, verify_token

    token = signed_token(7, 100000)
    assert verify_token(7, 100000, token) is True
    assert verify_token(7, 1, token) is False  # مبلغ جعلی
    assert verify_token(8, 100000, token) is False  # شناسهٔ جعلی

"""M110 — بانک صندباکس محلی: قرارداد، یک‌بارمصرفی، بازگشت وجه و قفل production.

چرا این فایل جدا از `test_q6_gateway.py` است: آن suite با `MockGateway` می‌چرخد که
هرگز «هدایت به بانک» و «وضعیت واقعیِ تراکنش پیش از verify» را ندارد — Mock به هر
authority خوش‌ساخت می‌گوید «پرداخت شد». بانک صندباکس یک سرویس HTTP مستقل است و
**حالت دارد**: تا وقتی انسان (یا آزمون) دکمهٔ «موفق» را نزده، verify می‌گوید ۱۰۳.
این همان چیزی است که هیچ‌وقت درون‌پروسه‌ای آزموده نمی‌شد.

آزمون‌ها شبکه/پورت نمی‌خواهند: `TestClient` همان اپ ASGI را درون‌پروسه اجرا می‌کند و
آداپتر هم **همان** آداپترِ واقعیِ production است (جز کلاینت تزریق‌شده).
"""

from __future__ import annotations

import itertools
import time
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from devtools import sandbox_bank

_counter = itertools.count(984001)


def _purchase(bank, amount=250_000, **over):
    body = {
        "merchant_id": sandbox_bank.BANK_MERCHANT_ID,
        "amount": amount,
        "description": "حق عضویت",
        "callback_url": "https://mp.test/api/v1/payments/1/callback",
        **over,
    }
    r = bank.post("/api/v1/purchase", json=body)
    assert r.status_code == 200, r.text
    return r.json()["data"]["authority"]


def _pay(bank, authority, outcome="success"):
    """کلیک روی دکمهٔ صفحهٔ بانک ← ۳۰۲ با query به سمت تاجر."""
    # follow_redirects=False: خودِ redirect پاسخِ آزمون است؛ اگر دنبال شود،
    # TestClient آدرس تاجر (بیرون از بانک) را به همان اپ بانک می‌زند و ۴۰۴ می‌گیرد.
    r = bank.post(f"/pay/{authority}", data={"outcome": outcome}, follow_redirects=False)
    assert r.status_code in (302, 307), (r.status_code, r.text)
    return parse_qs(urlparse(r.headers["location"]).query)


@pytest.fixture()
def bank():
    sandbox_bank._reset()
    client = TestClient(sandbox_bank.app, follow_redirects=False)
    yield client
    sandbox_bank._reset()


# ─────────────────────────── قرارداد بانک (بدون اپ ما) ───────────────────────────


def test_success_redirect_carries_authority_amount_and_signature(bank):
    authority = _purchase(bank, amount=123_456)
    q = _pay(bank, authority)
    assert q["Authority"] == [authority]
    assert q["Amount"] == ["123456"]
    assert q["Sign"] == [sandbox_bank._sign(authority, 123_456)]


def test_cancel_redirect_signs_nothing(bank):
    """انصراف کاربر: بانک برمی‌گرداند ولی چیزی را امضا نمی‌کند که تأیید نشده باشد."""
    authority = _purchase(bank)
    q = _pay(bank, authority, outcome="cancel")
    assert "Sign" not in q
    assert q["Authority"] == [authority]


def test_verify_is_single_use_and_replay_returns_same_reference(bank):
    authority = _purchase(bank)
    _pay(bank, authority)
    body = {
        "merchant_id": sandbox_bank.BANK_MERCHANT_ID,
        "authority": authority,
        "amount": 250_000,
    }
    first = bank.post("/api/v1/verify", json=body).json()
    assert first["result"]["status"] == 100
    second = bank.post("/api/v1/verify", json=body).json()
    assert second["result"]["status"] == 101
    assert second["data"]["ref_id"] == first["data"]["ref_id"]


def test_verify_amount_mismatch_is_102(bank):
    authority = _purchase(bank, amount=250_000)
    _pay(bank, authority)
    r = bank.post(
        "/api/v1/verify",
        json={
            "merchant_id": sandbox_bank.BANK_MERCHANT_ID,
            "authority": authority,
            "amount": 1,  # تاجرِ بدخواه/باگ‌دار
        },
    ).json()
    assert r["result"]["status"] == 102


def test_verify_unpaid_transaction_is_103(bank):
    """قلبِ کلیدی: authority ساخته شده ولی کاربر پرداخت نکرده — تأیید ممکن نیست."""
    authority = _purchase(bank)
    r = bank.post(
        "/api/v1/verify",
        json={
            "merchant_id": sandbox_bank.BANK_MERCHANT_ID,
            "authority": authority,
            "amount": 250_000,
        },
    ).json()
    assert r["result"]["status"] == 103


def test_expired_authority_verifies_as_minus_one(bank):
    authority = _purchase(bank, ttl_seconds=0)
    time.sleep(0.01)
    r = bank.post(
        "/api/v1/verify",
        json={
            "merchant_id": sandbox_bank.BANK_MERCHANT_ID,
            "authority": authority,
            "amount": 250_000,
        },
    ).json()
    assert r["result"]["status"] == -1


def test_refund_requires_verified_then_is_idempotent(bank):
    authority = _purchase(bank)
    body = {
        "merchant_id": sandbox_bank.BANK_MERCHANT_ID,
        "authority": authority,
        "amount": 250_000,
    }
    assert bank.post("/api/v1/refund", json=body).json()["result"]["status"] == 103
    _pay(bank, authority)
    bank.post("/api/v1/verify", json=body)
    done = bank.post("/api/v1/refund", json=body).json()
    assert done["result"]["status"] == 255 and done["data"]["ref_id"].startswith("SBXRFD-")
    again = bank.post("/api/v1/refund", json=body).json()
    assert again["result"]["status"] == 254
    assert again["data"]["ref_id"] == done["data"]["ref_id"]


def test_bank_rejects_unknown_merchant_and_bad_amounts(bank):
    r = bank.post("/api/v1/purchase", json={"merchant_id": "other", "amount": 10})
    assert r.status_code == 401
    assert (
        bank.post(
            "/api/v1/purchase",
            json={"merchant_id": sandbox_bank.BANK_MERCHANT_ID, "amount": 0},
        ).status_code
        == 422
    )
    assert bank.get("/pay/deadbeef").status_code == 404


# ───────────────────────────── آداپتر (واحد) ─────────────────────────────


def _adapter(http_client=None, base_url="http://bank.local", **kw):
    from modules.payments.gateway import SandboxBankAdapter

    return SandboxBankAdapter(
        base_url, sandbox_bank.BANK_MERCHANT_ID, http_client=http_client, **kw
    )


def test_adapter_maps_bank_5xx_to_unavailable_not_invalid(bank):
    """اهرم `http_error`: بانکِ خراب نباید «authority نامعتبر» به‌نظر برسد —
    معنایش فرق می‌کند: در دسترس نبودن ⇒ پرداخت pending می‌ماند و بعداً تأیید
    می‌شود؛ نامعتبر ⇒ باید fail شود. اشتباه‌گیری در این نگاشت، پول_member را می‌سوزاند."""
    from modules.payments.gateway import PaymentGatewayError

    txn = sandbox_bank.Txn(
        authority="t-5xx",
        amount_rial=100,
        description="",
        callback_url="",
        created_at=time.time(),
        ttl_seconds=60,
        state="paid",
        http_error=1,
    )
    sandbox_bank._LEDGER["t-5xx"] = txn
    with pytest.raises(PaymentGatewayError) as exc:
        _adapter(http_client=bank).verify("t-5xx", 100)
    assert exc.value.code == "gateway_unavailable"


def test_adapter_maps_unknown_authority_to_invalid(bank):
    from modules.payments.gateway import PaymentGatewayError

    with pytest.raises(PaymentGatewayError) as exc:
        _adapter(http_client=bank).verify("t-nope", 100)
    assert exc.value.code == "authority_not_found"


def test_adapter_unreachable_bank_is_gateway_unreachable():
    """پورت بسته = خطای شبکه؛ نه «ناموفق». (پورت ۱ روی loopback همیشه refuse می‌کند.)"""
    from modules.payments.gateway import PaymentGatewayError

    with pytest.raises(PaymentGatewayError) as exc:
        _adapter(base_url="http://127.0.0.1:1", timeout=0.5).start(100, "x", "https://c")
    assert exc.value.code == "gateway_unreachable"


def test_get_gateway_never_hands_out_sandbox_in_production(monkeypatch):
    from modules.payments.gateway import PaymentGatewayError, get_gateway

    monkeypatch.setattr(settings, "payment_gateway", "sandbox")
    monkeypatch.setattr(settings, "environment", "production")
    with pytest.raises(PaymentGatewayError):
        get_gateway()
    monkeypatch.setattr(settings, "environment", "development")
    monkeypatch.setattr(settings, "sandbox_bank_url", "")
    with pytest.raises(PaymentGatewayError) as exc:
        get_gateway()
    assert exc.value.code == "gateway_not_configured"


def test_production_settings_validator_names_the_sandbox():
    with pytest.raises(Exception) as exc:
        Settings(
            _env_file=None,
            environment="production",
            payment_gateway="sandbox",
            secret_key="x" * 40,
        )
    assert "sandbox" in str(exc.value)


# ─────────────────────── چرخهٔ کامل: اپ ما ↔ بانک صندباکس ───────────────────────


@pytest.fixture()
def client(tmp_path, monkeypatch, bank):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/sb.db")
    monkeypatch.setattr(settings, "payment_gateway", "sandbox")
    monkeypatch.setattr(settings, "sandbox_bank_url", "http://bank.local")
    monkeypatch.setattr(settings, "sandbox_bank_merchant_id", sandbox_bank.BANK_MERCHANT_ID)

    import modules.payments.gateway as gateway_mod

    monkeypatch.setattr(
        gateway_mod,
        "get_gateway",
        lambda: _adapter(http_client=TestClient(sandbox_bank.app, follow_redirects=False)),
    )

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
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


@pytest.fixture()
def admin_headers(client):
    """خلاصهٔ مالی عمداً برای پذیرش ۴۰۳ است (M59/R3) — این تست با admin می‌خواندش."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"a{n}", role="admin")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


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


def _paid_payment(client, bank, h, member_id, amount=250_000):
    p = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": amount, "method": "zarinpal"},
        headers=h,
    ).json()
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()
    assert start["redirect_url"] == f"http://bank.local/pay/{start['authority']}"
    q = _pay(bank, start["authority"])
    assert q["Sign"] == [sandbox_bank._sign(start["authority"], amount)]
    r = client.post(
        f"/api/v1/payments/{p['id']}/callback",
        json={"authority": start["authority"], "callback_token": start["callback_token"]},
        headers=h,
    )
    assert r.status_code == 200, r.text
    return p["id"], r.json()


def test_full_cycle_through_the_bank(client, bank, reception, member_id):
    """شروع در اپ ما →authority بانک → کلیک «موفق» → redirect امضاشده → callback →
    verify **واقعاً در بانک** → paid با کد پیگیری بانک."""
    h = reception
    pid, body = _paid_payment(client, bank, h, member_id)
    assert body["status"] == "paid"
    assert body["reference_id"].startswith("SBXREF-")
    st = bank.get(f"/api/v1/status/{body['gateway_authority']}").json()
    assert st["verified"] and st["state"] == "paid"


def test_callback_without_bank_payment_cannot_settle(client, bank, reception, member_id):
    """اعتبارِ پول، بیرون از اپ ماست: token درست + authority درست + پرداخت **نکرده**
    ⇒ تأیید نمی‌شود. MockGateway این حالت را اصلاً نمی‌تواند بازproduce کند."""
    h = reception
    p = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 300_000, "method": "zarinpal"},
        headers=h,
    ).json()
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()
    r = client.post(
        f"/api/v1/payments/{p['id']}/callback",
        json={"authority": start["authority"], "callback_token": start["callback_token"]},
        headers=h,
    )
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "not_paid_at_bank"
    again = client.get(f"/api/v1/payments?member_id={member_id}", headers=h).json()[0]
    assert again["status"] == "pending"


def test_cancelled_at_bank_then_failed_locally(client, bank, reception, member_id):
    h = reception
    p = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 120_000, "method": "zarinpal"},
        headers=h,
    ).json()
    start = client.post(f"/api/v1/payments/{p['id']}/start", json={}, headers=h).json()
    q = _pay(bank, start["authority"], outcome="cancel")
    assert "Sign" not in q
    settle = client.post(
        f"/api/v1/payments/{p['id']}/callback",
        json={"authority": start["authority"], "callback_token": start["callback_token"]},
        headers=h,
    )
    assert settle.status_code == 400  # بانک می‌گوید ۱۰۳ — امضای ما کافی نیست
    assert client.post(f"/api/v1/payments/{p['id']}/fail", headers=h).json()["status"] == "failed"


def test_refund_marks_refunded_and_finance_subtracts_it(
    client, bank, reception, admin_headers, member_id
):
    h, fin = reception, admin_headers
    pid, body = _paid_payment(client, bank, h, member_id)
    assert body["status"] == "paid"

    assert client.get("/api/v1/payments/finance/summary", headers=h).status_code == 403
    before = client.get("/api/v1/payments/finance/summary", headers=fin).json()
    assert before["total_paid_rial"] >= 250_000

    r = client.post(f"/api/v1/payments/{pid}/refund", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "refunded"

    after = client.get("/api/v1/payments/finance/summary", headers=fin).json()
    assert after["total_paid_rial"] == before["total_paid_rial"] - 250_000
    assert after["total_refunded_rial"] == before["total_refunded_rial"] + 250_000
    assert after["refunded_count"] == 1

    listing = client.get("/api/v1/payments?status=refunded", headers=h).json()
    assert [x["id"] for x in listing] == [pid]

    again = client.post(f"/api/v1/payments/{pid}/refund", headers=h)
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "already_refunded"

    st = bank.get(f"/api/v1/status/{body['gateway_authority']}").json()
    assert st["refunded"] and st["state"] == "refunded"


def test_wallet_and_pending_payments_are_not_refundable(client, bank, reception, member_id):
    h = reception
    ch = client.post(
        "/api/v1/payments/wallet/charge",
        json={"member_id": member_id, "amount_rial": 50_000},
        headers=h,
    )
    assert ch.status_code == 200, ch.text
    w = client.post(
        "/api/v1/payments/wallet/pay",
        json={"member_id": member_id, "amount_rial": 10_000},
        headers=h,
    )
    assert w.status_code == 200, w.text
    wid = w.json()["id"]
    r = client.post(f"/api/v1/payments/{wid}/refund", headers=h)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "wallet_not_gateway"

    p = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 50_000, "method": "zarinpal"},
        headers=h,
    ).json()
    r2 = client.post(f"/api/v1/payments/{p['id']}/refund", headers=h)
    assert r2.status_code == 400
    assert r2.json()["error"]["code"] == "not_refundable"  # پرداخت‌نشده برگشت ندارد


def test_mock_gateway_has_no_refund_path(client, monkeypatch, reception, member_id):
    """refunded یک مسیر درگاهی است؛ Mock عمداً refund ندارد تا پولِ آزمایشیِ درون‌پروسه
    با «بازگشت داده‌شده» اشتباه گرفته نشود — درگاه باید صریحاً پشتیبانی کند."""
    from db.base import get_session_factory
    from db.models import Payment

    h = reception
    p = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 40_000, "method": "zarinpal"},
        headers=h,
    ).json()
    with get_session_factory()() as s:
        row = s.get(Payment, p["id"])
        row.status = "paid"
        row.gateway_authority = "MOCK-9c40-ffff0000"
        s.commit()
    import modules.payments.gateway as gateway_mod

    monkeypatch.setattr(gateway_mod, "get_gateway", lambda: gateway_mod.MockGateway())
    r = client.post(f"/api/v1/payments/{p['id']}/refund", headers=h)
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "refund_unsupported"


# ─────────────── چرخهٔ انسانی: مرورگر ↔ بانک ↔ مسیر عمومی بازگشت ───────────────


def _browser(client, bank, h, member_id, outcome="success", amount=180_000):
    """اپ هیچ نقشی در این چرخه ندارد؛ فقط start گرفته می‌شود و بقیه مرورگر است."""
    from app.config import settings as st

    st_snapshot = st.public_base_url
    st.public_base_url = "http://app.test"
    try:
        pay = client.post(
            "/api/v1/payments",
            json={"member_id": member_id, "amount_rial": amount, "method": "zarinpal"},
            headers=h,
        ).json()
        start = client.post(f"/api/v1/payments/{pay['id']}/start", json={}, headers=h).json()
        path = urlparse(start["redirect_url"]).path
        page = bank.get(path)
        assert page.status_code == 200 and "پرداخت موفق" in page.text
        red = bank.post(path, data={"outcome": outcome}, follow_redirects=False)
        assert red.status_code == 302  # نه ۳۰۷ — بانک واقعی GET برمی‌گرداند
        return pay["id"], urlparse(red.headers["location"])
    finally:
        st.public_base_url = st_snapshot


def test_human_browser_flow_settles_on_public_return(client, bank, reception, member_id):
    h = reception
    pid, loc = _browser(client, bank, h, member_id)
    assert loc.path == f"/api/v1/payments/{pid}/gateway-return"
    q = parse_qs(loc.query)
    assert q["Amount"] == ["180000"] and q["Sign"] == [
        sandbox_bank._sign(q["Authority"][0], 180_000)
    ]
    settle = client.get(loc.path, params={"Authority": q["Authority"][0], "token": q["token"][0]})
    assert settle.status_code == 200 and "پرداخت تأیید شد" in settle.text
    row = client.get(f"/api/v1/payments?member_id={member_id}", headers=h).json()[0]
    assert row["status"] == "paid" and row["reference_id"].startswith("SBXREF-")

    # رفرش مرورگر = replayِ همین redirect؛ پول یک بار ثبت می‌شود و صفحه خطا نمی‌دهد
    again = client.get(loc.path, params={"Authority": q["Authority"][0], "token": q["token"][0]})
    assert again.status_code == 200 and "قبلاً ثبت" in again.text


def test_forged_return_renders_error_and_does_not_settle(client, bank, reception, member_id):
    """مسیر عمومی است، ولی بدون tokenِ امضاشده هرگز تسویه نمی‌کند."""
    h = reception
    pid, loc = _browser(client, bank, h, member_id, outcome="cancel")
    r = client.get(loc.path, params={"Authority": "a" * 16, "token": "f" * 32})
    assert r.status_code == 200 and "تأیید نشد" in r.text
    row = client.get(f"/api/v1/payments?member_id={member_id}", headers=h).json()[0]
    assert row["id"] == pid and row["status"] == "pending"


def test_valid_token_but_cancelled_at_bank_still_not_settleable(client, bank, reception, member_id):
    """انصراف کاربر: token ما درست است، authority هم درست — اما بانک پرداخت را
    تأیید نمی‌کند ⇒ تسویه نیست. دقیقاً همان درسی که Mock به آدم نمی‌دهد."""
    h = reception
    pid, loc = _browser(client, bank, h, member_id, outcome="cancel")
    q = parse_qs(loc.query)
    r = client.get(loc.path, params={"Authority": q["Authority"][0], "token": q["token"][0]})
    assert "تأیید نشد" in r.text
    row = client.get(f"/api/v1/payments?member_id={member_id}", headers=h).json()[0]
    assert row["status"] == "pending"

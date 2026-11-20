"""G2 — کد تخفیف: درصدی/مبلغ ثابت، انقضا، سقف استفاده، idempotency.

# قرارداد (بند ۲.۲ پلن: هر تغییر پول با سناریوی زنده)
| # | سناریو | انتظار |
|---|---|---|
| ۱ | کوپن درصدی روی پرداخت | مبلغ خالص = مبلغ − درصد؛ `discount_rial` ثبت می‌شود |
| ۲ | کوپن مبلغ ثابت | مبلغ خالص = مبلغ − مبلغ ثابت |
| ۳ | کد نامعتبر | ۴۰۰ `coupon_invalid`، پرداختی ساخته نمی‌شود |
| ۴ | کد منقضی | ۴۰۰ `coupon_expired` |
| ۵ | سقف استفاده پر | ۴۰۰ `coupon_exhausted`؛ شمارنده بالا نمی‌رود |
| ۶ | کلید تکراری (idempotency) | همان پرداخت؛ کوپن دوبار مصرف نمی‌شود |
| ۷ | مبلغ پس از تخفیف زیر حداقل | ۴۰۰ `coupon_amount_too_low` |
| ۸ | عضو کد تخفیف جدید بسازد | ۴۰۳ (فقط کادر با `finance.write`) |
| ۹ | کد تکراری | ۴۰۹ |
| ۱۰ | درصد خارج از ۱..۱۰۰ | ۴۲۲/۴۰۰ اعتبارسنجی |

# آنچه این تست ثابت نمی‌کند
- همزمانی واقعی چند درخواست روی PostgreSQL (تست روی SQLite است؛ UPDATE شرطی همان منطق را دارد).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.security.jwt import decode_access_token
from db.base import get_session_factory
from db.models import Coupon, Member, Payment
from tests.integration._actors import create_actor

BASE = 2_000_000


def _member() -> tuple[int, dict]:
    headers = create_actor("member")
    user_id = int(decode_access_token(headers["Authorization"].split(" ", 1)[1])["sub"])
    with get_session_factory()() as s:
        member = Member(user_id=user_id, goal="hypertrophy", constraints="[]")
        s.add(member)
        s.commit()
        return member.id, headers


def _staff() -> dict:
    return create_actor("manager", ["finance.write"])


def _make_coupon(client: TestClient, staff: dict, **body) -> dict:
    payload = {"code": "SPRING10", "kind": "percent", "value": 10}
    payload.update(body)
    res = client.post("/api/v1/payments/coupons", json=payload, headers=staff)
    assert res.status_code == 201, res.text
    return res.json()


def _pay(client: TestClient, headers: dict, member_id: int, **extra):
    body = {"member_id": member_id, "amount_rial": BASE, "method": "cash"}
    body.update(extra)
    return client.post("/api/v1/payments", json=body, headers=headers)


def test_percent_coupon_discounts_amount_on_server(client: TestClient) -> None:
    staff = _staff()
    coupon = _make_coupon(client, staff)
    member_id, mh = _member()
    res = _pay(client, mh, member_id, coupon_code="spring10")  # کوچک‌وبزرگ‌حروف مهم نیست
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["amount_rial"] == BASE - BASE * 10 // 100
    assert body["discount_rial"] == BASE * 10 // 100
    assert body["coupon_id"] == coupon["id"]


def test_fixed_coupon_subtracts_rial_amount(client: TestClient) -> None:
    staff = _staff()
    _make_coupon(client, staff, code="FIX500", kind="fixed", value=500_000)
    member_id, mh = _member()
    body = _pay(client, mh, member_id, coupon_code="FIX500").json()
    assert body["amount_rial"] == 1_500_000
    assert body["discount_rial"] == 500_000


def test_unknown_code_creates_no_payment(client: TestClient) -> None:
    member_id, mh = _member()
    res = _pay(client, mh, member_id, coupon_code="NOPE123")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "coupon_invalid"
    with get_session_factory()() as s:
        assert s.scalar(select(Payment).where(Payment.member_id == member_id)) is None


def test_expired_coupon_is_rejected(client: TestClient) -> None:
    staff = _staff()
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat()
    _make_coupon(client, staff, code="OLD10", expires_at=past)
    member_id, mh = _member()
    res = _pay(client, mh, member_id, coupon_code="OLD10")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "coupon_expired"


def test_usage_cap_blocks_second_use(client: TestClient) -> None:
    staff = _staff()
    _make_coupon(client, staff, code="ONCE", max_uses=1)
    member_id, mh = _member()
    assert _pay(client, mh, member_id, coupon_code="ONCE").status_code == 200
    res = _pay(client, mh, member_id, coupon_code="ONCE")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "coupon_exhausted"
    with get_session_factory()() as s:
        coupon = s.scalar(select(Coupon).where(Coupon.code == "ONCE"))
        assert coupon.used_count == 1


def test_idempotent_retry_does_not_consume_coupon_twice(client: TestClient) -> None:
    staff = _staff()
    _make_coupon(client, staff, code="TWICE", max_uses=5)
    member_id, mh = _member()
    key = "idem-g2-0001"
    first = _pay(client, mh, member_id, coupon_code="TWICE", idempotency_key=key)
    second = _pay(client, mh, member_id, coupon_code="TWICE", idempotency_key=key)
    assert first.json()["id"] == second.json()["id"]
    with get_session_factory()() as s:
        coupon = s.scalar(select(Coupon).where(Coupon.code == "TWICE"))
        assert coupon.used_count == 1


def test_discount_below_minimum_is_rejected(client: TestClient) -> None:
    staff = _staff()
    _make_coupon(client, staff, code="HUGE", kind="fixed", value=1_999_500)
    member_id, mh = _member()
    res = _pay(client, mh, member_id, coupon_code="HUGE")
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "coupon_amount_too_low"


def test_member_cannot_create_coupon(client: TestClient) -> None:
    _, mh = _member()
    res = client.post(
        "/api/v1/payments/coupons",
        json={"code": "MINE", "kind": "percent", "value": 100},
        headers=mh,
    )
    assert res.status_code == 403


def test_duplicate_code_conflicts(client: TestClient) -> None:
    staff = _staff()
    _make_coupon(client, staff, code="DUP")
    res = client.post(
        "/api/v1/payments/coupons",
        json={"code": "dup", "kind": "percent", "value": 5},
        headers=staff,
    )
    assert res.status_code == 409


def test_percent_out_of_range_is_rejected(client: TestClient) -> None:
    staff = _staff()
    res = client.post(
        "/api/v1/payments/coupons",
        json={"code": "TOOBIG", "kind": "percent", "value": 150},
        headers=staff,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "coupon_value_invalid"

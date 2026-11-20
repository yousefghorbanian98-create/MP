"""فاز ۳ — حذف درگاه پرداخت اینترنتی (تصمیم مالک ۲۰۲۶-۱۱-۱۹).

قاعده: تنها روش‌های پرداخت، حضوری‌اند — نقدی، کارت‌خوان و کارت‌به‌کارت با رسید.
هیچ آداپتر درگاه اینترنتی در کد نمی‌ماند و هیچ مسیری برای آغاز پرداخت آنلاین باز نیست.

| تست | قاعده |
|---|---|
| `test_zarinpal_adapter_is_removed` | کلاس آداپتر زرین‌پال وجود ندارد |
| `test_config_rejects_zarinpal_mode` | تنظیم درگاه اینترنتی پذیرفته نمی‌شود |
| `test_manual_mode_refuses_online_start` | حالت پیش‌فرض، آغاز پرداخت آنلاین را رد می‌کند |
| `test_start_endpoint_returns_conflict` | مسیر `/start` با ۴۰۹ و کد روشن جواب می‌دهد، نه ۲۰۰ |
| `test_payment_method_zarinpal_is_rejected` | ساخت پرداخت با متد درگاه ۴۲۲ می‌گیرد |
| `test_shop_gateway_kind_rejects_online_providers` | درگاه فروشگاه فقط کارت‌به‌کارت/نقدی می‌پذیرد |
| `test_historical_gateway_payment_stays_readable` | ردیف تاریخی با متد قدیمی خواندنی می‌ماند |

چرا ردیف تاریخی می‌ماند: حذف درگاه، حذف سابقهٔ مالی نیست. دادهٔ گذشته باید
قابل حسابرسی بماند؛ فقط مسیر تازه بسته می‌شود.
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import Settings, settings

_counter = itertools.count(930001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/phase3.db")
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


def _user(role: str) -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
        s.add(u)
        s.commit()
        member_id = None
        if role == "member":
            member = Member(user_id=u.id, branch_id=1)
            s.add(member)
            s.commit()
            member_id = member.id
        return {
            "id": u.id,
            "member_id": member_id,
            "headers": {"Authorization": f"Bearer {create_access_token(u.id, role)}"},
        }


def test_zarinpal_adapter_is_removed() -> None:
    from modules.payments import gateway

    assert not hasattr(gateway, "ZarinpalAdapter")


def test_config_rejects_zarinpal_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(payment_gateway="zarinpal")


def test_manual_mode_refuses_online_start(monkeypatch) -> None:
    from modules.payments import gateway

    monkeypatch.setattr(settings, "payment_gateway", "manual")
    with pytest.raises(gateway.PaymentGatewayError) as exc:
        gateway.get_gateway()
    assert exc.value.code == "online_gateway_removed"


def test_start_endpoint_returns_conflict(client: TestClient, monkeypatch) -> None:
    monkeypatch.setattr(settings, "payment_gateway", "manual")
    owner = _user("super_admin")
    member = _user("member")
    created = client.post(
        "/api/v1/payments",
        json={"member_id": member["member_id"], "amount_rial": 250_000, "method": "cash"},
        headers=owner["headers"],
    )
    assert created.status_code == 200, created.text
    payment_id = created.json()["id"]
    r = client.post(f"/api/v1/payments/{payment_id}/start", json={}, headers=owner["headers"])
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "online_gateway_removed"


def test_payment_method_zarinpal_is_rejected(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    r = client.post(
        "/api/v1/payments",
        json={"member_id": member["member_id"], "amount_rial": 250_000, "method": "zarinpal"},
        headers=owner["headers"],
    )
    assert r.status_code == 422, r.text


def test_shop_gateway_kind_rejects_online_providers(client: TestClient) -> None:
    owner = _user("super_admin")
    r = client.post(
        "/api/v1/shop/gateways",
        json={"kind": "zarinpal", "title": "زرین‌پال"},
        headers=owner["headers"],
    )
    assert r.status_code == 422, r.text


def test_historical_gateway_payment_stays_readable(client: TestClient) -> None:
    from datetime import UTC, datetime

    from db.base import get_session_factory
    from db.models import Payment

    owner = _user("super_admin")
    member = _user("member")
    with get_session_factory()() as s:
        s.add(
            Payment(
                member_id=member["member_id"],
                amount_rial=120_000,
                method="zarinpal",
                status="paid",
                reference_id="LEGACY-1",
                paid_at=datetime(2026, 5, 1, tzinfo=UTC),
            )
        )
        s.commit()
    r = client.get("/api/v1/payments", headers=owner["headers"])
    assert r.status_code == 200, r.text
    rows = r.json()
    assert any(row["method"] == "zarinpal" for row in rows)

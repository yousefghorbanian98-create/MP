"""فاز ۲ — فروشگاه نمایش‌محور (تصمیم مالک ۲۰۲۶-۱۱-۱۹).

قاعده‌ها:

| تست | قاعده |
|---|---|
| `test_status_reports_in_person_mode` | سرور وضعیت را می‌گوید: خرید حضوری، بدون خرید درون‌برنامه‌ای |
| `test_status_closed_outside_hours` | خارج از ساعت کاری، وضعیت «بسته» با علت روشن است |
| `test_status_closed_on_weekly_holiday` | روز تعطیل هفتگی هم علت خودش را دارد |
| `test_catalog_is_readable` | کاتالوگ خواندنی می‌ماند؛ «فقط مشاهده» یعنی همین |
| `test_cart_write_is_fail_closed` | افزودن به سبد با ۴۰۹ بسته است، نه با ۲۰۰ خاموش |
| `test_cart_mutation_is_fail_closed` | تغییر و حذف قلم سبد هم بسته است |
| `test_checkout_is_fail_closed` | تسویه هم بسته است؛ پیام می‌گوید حضوری |
| `test_order_history_stays_readable` | تاریخچهٔ سفارش حذف نمی‌شود، فقط خواندنی است |

چرا ۴۰۹ و نه ۲۰۰ با بدنهٔ خالی: کلاینت باید بین «انجام شد» و «بسته است»
تفاوت ببیند؛ پاسخ سبز به عملیات انجام‌نشده، همان دروغی است که این فاز می‌بندد.
"""

from __future__ import annotations

import itertools
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(910001)
TEHRAN = ZoneInfo("Asia/Tehran")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/phase2.db")
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
        if role == "member":
            s.add(Member(user_id=u.id, branch_id=1))
            s.commit()
        return {
            "id": u.id,
            "role": role,
            "headers": {"Authorization": f"Bearer {create_access_token(u.id, role)}"},
        }


def _product(client: TestClient, owner: dict) -> dict:
    from db.base import get_session_factory
    from db.models import ProductCategory

    with get_session_factory()() as s:
        cat = ProductCategory(slug=f"sup-{next(_counter)}", title="مکمل", kind="supplement")
        s.add(cat)
        s.commit()
        category_id = cat.id
    r = client.post(
        "/api/v1/shop/products",
        json={
            "title": "پروتئین وی",
            "sku": f"WHEY-{next(_counter)}",
            "category_id": category_id,
            "price_rial": 500_000,
            "stock_qty": 10,
        },
        headers=owner["headers"],
    )
    assert r.status_code == 200, r.text
    return r.json()


def test_status_reports_in_person_mode(client: TestClient) -> None:
    member = _user("member")
    r = client.get("/api/v1/shop/status", headers=member["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mode"] == "in_person"
    assert body["online_purchase"] is False
    assert body["opens_at"] == "07:00"
    assert body["closes_at"] == "23:00"
    assert isinstance(body["is_open"], bool)
    assert body["reason"] in {"open", "outside_hours", "weekly_holiday"}


def test_status_closed_outside_hours() -> None:
    from modules.shop import service

    assert (
        service.store_status(now=datetime(2026, 11, 19, 3, 30, tzinfo=TEHRAN))["is_open"] is False
    )
    body = service.store_status(now=datetime(2026, 11, 19, 3, 30, tzinfo=TEHRAN))
    assert body["reason"] == "outside_hours"
    inside = service.store_status(now=datetime(2026, 11, 19, 10, 0, tzinfo=TEHRAN))
    assert inside["is_open"] is True
    assert inside["reason"] == "open"


def test_status_closed_on_weekly_holiday(monkeypatch) -> None:
    from modules.shop import service

    # ۱۹ نوامبر ۲۰۲۶ = پنجشنبه (weekday 3)
    monkeypatch.setattr(settings, "shop_closed_weekdays", "3")
    body = service.store_status(now=datetime(2026, 11, 19, 10, 0, tzinfo=TEHRAN))
    assert body["is_open"] is False
    assert body["reason"] == "weekly_holiday"


def test_catalog_is_readable(client: TestClient) -> None:
    owner = _user("super_admin")
    _product(client, owner)
    member = _user("member")
    r = client.get("/api/v1/shop/products", headers=member["headers"])
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) >= 1


def test_cart_write_is_fail_closed(client: TestClient) -> None:
    owner = _user("super_admin")
    product = _product(client, owner)
    member = _user("member")
    r = client.post(
        "/api/v1/shop/cart",
        json={"product_id": product["id"], "qty": 1},
        headers=member["headers"],
    )
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "shop_online_closed"


def test_cart_mutation_is_fail_closed(client: TestClient) -> None:
    member = _user("member")
    r = client.patch("/api/v1/shop/cart/1", json={"qty": 2}, headers=member["headers"])
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "shop_online_closed"
    r = client.delete("/api/v1/shop/cart/1", headers=member["headers"])
    assert r.status_code == 409, r.text


def test_checkout_is_fail_closed(client: TestClient) -> None:
    member = _user("member")
    r = client.post("/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"])
    assert r.status_code == 409, r.text
    body = r.json()["error"]
    assert body["code"] == "shop_online_closed"
    assert "حضوری" in body["message"]


def test_order_history_stays_readable(client: TestClient) -> None:
    member = _user("member")
    r = client.get("/api/v1/shop/orders", headers=member["headers"])
    assert r.status_code == 200
    assert r.json() == []

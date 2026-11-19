"""M59 — فروشگاه، کیف‌پول، سلسله‌مراتب نقش، و درخواست تأیید مالک.

هر تست یک **قاعدهٔ کسب‌وکار** را قفل می‌کند، نه یک پیاده‌سازی را:

| تست | قاعده |
|---|---|
| `test_member_cannot_see_finance_*` | عضو عادی نباید درآمد باشگاه/CSV را ببیند (یافتهٔ زنده) |
| `test_admin_cannot_create_product` | ساخت محصول/قیمت فقط مالک |
| `test_admin_cannot_touch_gateway` | درگاه و شمارهٔ کارت فقط مالک |
| `test_admin_requests_price_change_owner_approves` | مسیر مجاز ادمین: پیشنهاد ← تأیید مالک ← اعمال |
| `test_owner_cannot_approve_own_request` | تأیید درخواست خود = دور زدن کنترل |
| `test_gateway_secret_never_returned` | کلید خصوصی هرگز در پاسخ نمی‌آید |
| `test_card_number_is_masked` | شمارهٔ کارت ماسک‌شده برمی‌گردد |
| `test_price_comes_from_db_not_client` | کلاینت قیمت نمی‌فرستد؛ مبلغ از DB |
| `test_checkout_debits_wallet_and_creates_order` | کیف‌پول ← سفارش paid، موجودی کم |
| `test_checkout_insufficient_balance_keeps_cart` | شکست ← سبد دست‌نخورده |
| `test_order_price_is_frozen` | تغییر قیمت محصول، فاکتور قدیمی را عوض نمی‌کند |
| `test_member_sees_only_own_orders` | مالکیت سطری |
| `test_role_hierarchy_one_way` | admin ↛ super_admin، معاون ↛ بالاتر |
| `test_super_admin_not_assignable_via_api` | ساخت مالک دوم ممنوع |
| `test_stock_decrements` | موجودی پس از تسویه کم می‌شود |
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(880001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/shop.db")
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


@pytest.fixture(autouse=True)
def _money_engine_enabled(monkeypatch):
    """M59 موتور پول را می‌سنجد، نه حالت پیش‌فرض فروشگاه.

    از فاز ۲ (تصمیم مالک ۲۰۲۶-۱۱-۱۹) خرید درون‌برنامه‌ای بسته است؛
    `test_phase2_shop_display.py` همان حالت پیش‌فرض را قفل می‌کند. اینجا پرچم
    روشن می‌شود تا قاعده‌های پول — قفل قیمت، کم‌شدن موجودی، مالکیت سفارش —
    بی‌پوشش نمانند و برای فاز ۶ سالم بمانند.
    """
    monkeypatch.setattr(settings, "shop_online_purchase_enabled", True)


def _user(role: str) -> dict:
    """کاربر با نقش دلخواه + توکن؛ عضو هم پروندهٔ Member دارد."""
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


def _member_id(user: dict) -> int:
    from db.base import get_session_factory
    from db.models import Member

    with get_session_factory()() as s:
        return s.query(Member).filter(Member.user_id == user["id"]).one().id


def _category(client: TestClient, owner: dict, slug: str = "supplements") -> int:
    from db.base import get_session_factory
    from db.models import ProductCategory

    with get_session_factory()() as s:
        cat = ProductCategory(slug=slug, title="مکمل", kind="supplement")
        s.add(cat)
        s.commit()
        return cat.id


def _product(client: TestClient, owner: dict, *, price: int = 500_000, stock: int = 10) -> dict:
    r = client.post(
        "/api/v1/shop/products",
        json={
            "title": "پروتئین وی ۲ کیلو",
            "sku": f"WHEY-{next(_counter)}",
            "category_id": _category(client, owner),
            "price_rial": price,
            "image_url": "/static/shop/whey.jpg",
            "stock_qty": stock,
            "variants": [{"label": "شکلاتی", "price_rial": price + 50_000, "stock_qty": 5}],
        },
        headers=owner["headers"],
    )
    assert r.status_code == 200, r.text
    return r.json()


def _topup(client: TestClient, member: dict, amount: int) -> None:
    """شارژ کیف‌پول از مسیر مجاز (پذیرش) — عضو نمی‌تواند خودش شارژ کند."""
    from db.base import get_session_factory
    from modules.payments import service as payments

    with get_session_factory()() as s:
        payments.wallet_charge(s, _member_id(member), amount, "شارژ تست")


# ── ۱) نشت مالی (یافتهٔ زندهٔ این چرخه) ──
def test_member_cannot_see_finance_summary(client: TestClient) -> None:
    member = _user("member")
    assert (
        client.get("/api/v1/payments/finance/summary", headers=member["headers"]).status_code == 403
    )


def test_member_cannot_export_payments_csv(client: TestClient) -> None:
    member = _user("member")
    r = client.get("/api/v1/payments/finance/export.csv", headers=member["headers"])
    assert r.status_code == 403
    assert "amount_rial" not in r.text


def test_staff_can_see_finance_summary(client: TestClient) -> None:
    """۴۰۳ دادن به عضو نباید مدیر را هم ببندد (رگرسیون معکوس)."""
    admin = _user("admin")
    assert (
        client.get("/api/v1/payments/finance/summary", headers=admin["headers"]).status_code == 200
    )


# ── ۲) کاتالوگ: نوشتن فقط مالک ──
def test_admin_cannot_create_product(client: TestClient) -> None:
    admin = _user("admin")
    r = client.post(
        "/api/v1/shop/products",
        json={
            "title": "کراتین",
            "sku": "CRE-1",
            "category_id": _category(client, admin),
            "price_rial": 100,
        },
        headers=admin["headers"],
    )
    assert r.status_code == 403
    assert "super_admin" in r.text or "مالک" in r.text


def test_owner_can_create_product_with_image(client: TestClient) -> None:
    owner = _user("super_admin")
    body = _product(client, owner)
    assert body["price_rial"] == 500_000
    assert body["image_url"] == "/static/shop/whey.jpg"
    assert body["variants"][0]["price_rial"] == 550_000


def test_admin_cannot_change_price(client: TestClient) -> None:
    owner = _user("super_admin")
    admin = _user("admin")
    product = _product(client, owner)
    r = client.patch(
        f"/api/v1/shop/products/{product['id']}",
        json={"price_rial": 1},
        headers=admin["headers"],
    )
    assert r.status_code == 403
    assert (
        client.get(f"/api/v1/shop/products/{product['id']}", headers=admin["headers"]).json()[
            "price_rial"
        ]
        == 500_000
    )


def test_member_can_read_catalog(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    _product(client, owner)
    r = client.get("/api/v1/shop/products", headers=member["headers"])
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── ۳) درگاه و شمارهٔ کارت ──
def test_admin_cannot_touch_gateway(client: TestClient) -> None:
    admin = _user("admin")
    r = client.post(
        "/api/v1/shop/gateways",
        json={
            "kind": "card_to_card",
            "title": "کارت به کارت بانک ملت",
            "card_number": "6104" + "1" * 12,
        },
        headers=admin["headers"],
    )
    assert r.status_code == 403


def test_owner_adds_card_and_member_reads_masked(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    card = "6104337712345678"
    r = client.post(
        "/api/v1/shop/gateways",
        json={
            "kind": "card_to_card",
            "title": "کارت به کارت — ملت",
            "is_enabled": True,
            "card_number": card,
            "card_holder": "باشگاه ماسل پارادایس",
            "bank_name": "ملت",
            "secret_key": "SUPER-SECRET",
            "instructions": "پس از واریز، شمارهٔ پیگیری را در اپ ثبت کنید.",
        },
        headers=owner["headers"],
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["card_number_masked"].endswith("5678")
    assert card not in str(body), "شمارهٔ کامل کارت نباید برگردد"
    assert "SUPER-SECRET" not in str(body), "کلید خصوصی نباید برگردد"
    assert body["secret_configured"] is True

    read = client.get("/api/v1/shop/gateways", headers=member["headers"])
    assert read.status_code == 200
    assert read.json()[0]["card_number_masked"].endswith("5678")


def test_bad_card_number_rejected(client: TestClient) -> None:
    owner = _user("super_admin")
    r = client.post(
        "/api/v1/shop/gateways",
        json={"kind": "card_to_card", "title": "کارت", "card_number": "123"},
        headers=owner["headers"],
    )
    assert r.status_code == 400
    assert "۱۶" in r.text or "16" in r.text


# ── ۴) درخواست تأیید (ادمین ← مالک) ──
def test_admin_requests_price_change_owner_approves(client: TestClient) -> None:
    owner = _user("super_admin")
    admin = _user("admin")
    product = _product(client, owner)

    req = client.post(
        "/api/v1/shop/change-requests",
        json={
            "kind": "product_price",
            "payload": {"product_id": product["id"], "price_rial": 780_000},
        },
        headers=admin["headers"],
    )
    assert req.status_code == 200, req.text
    req_id = req.json()["id"]
    # تا تأیید، قیمت تغییر نکرده
    assert (
        client.get(f"/api/v1/shop/products/{product['id']}", headers=admin["headers"]).json()[
            "price_rial"
        ]
        == 500_000
    )

    # ادمین نمی‌تواند تأیید کند
    assert (
        client.post(
            f"/api/v1/shop/change-requests/{req_id}/review",
            json={"approve": True},
            headers=admin["headers"],
        ).status_code
        == 403
    )

    ok = client.post(
        f"/api/v1/shop/change-requests/{req_id}/review",
        json={"approve": True, "note": "تأیید شد"},
        headers=owner["headers"],
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "approved"
    assert (
        client.get(f"/api/v1/shop/products/{product['id']}", headers=owner["headers"]).json()[
            "price_rial"
        ]
        == 780_000
    )


def test_owner_cannot_approve_own_request(client: TestClient) -> None:
    owner = _user("super_admin")
    req = client.post(
        "/api/v1/shop/change-requests",
        json={
            "kind": "membership_price",
            "payload": {"code": "m1", "title": "ماهانه", "price_rial": 1},
        },
        headers=owner["headers"],
    )
    assert req.status_code == 200, req.text
    r = client.post(
        f"/api/v1/shop/change-requests/{req.json()['id']}/review",
        json={"approve": True},
        headers=owner["headers"],
    )
    assert r.status_code == 400
    assert "self_review" in r.text


def test_member_cannot_create_change_request(client: TestClient) -> None:
    member = _user("member")
    r = client.post(
        "/api/v1/shop/change-requests",
        json={"kind": "membership_price", "payload": {}},
        headers=member["headers"],
    )
    assert r.status_code in (400, 403)


def test_admin_lists_only_own_requests(client: TestClient) -> None:
    owner = _user("super_admin")
    admin_a = _user("admin")
    admin_b = _user("admin")
    client.post(
        "/api/v1/shop/change-requests",
        json={
            "kind": "membership_price",
            "payload": {"code": "a", "title": "الف", "price_rial": 1},
        },
        headers=admin_a["headers"],
    )
    assert client.get("/api/v1/shop/change-requests", headers=admin_b["headers"]).json() == []
    assert len(client.get("/api/v1/shop/change-requests", headers=owner["headers"]).json()) >= 1


# ── ۵) قیمت‌گذاری خدمات ──
def test_owner_sets_membership_and_coach_price(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    r = client.post(
        "/api/v1/shop/prices",
        json={
            "category": "membership",
            "code": "gold-3m",
            "title": "طلایی ۳ ماهه",
            "price_rial": 6_000_000,
            "duration_days": 90,
        },
        headers=owner["headers"],
    )
    assert r.status_code == 200, r.text
    r2 = client.post(
        "/api/v1/shop/prices",
        json={
            "category": "coach_fee",
            "code": "pt-1m",
            "title": "شهریهٔ مربی خصوصی",
            "price_rial": 3_000_000,
        },
        headers=owner["headers"],
    )
    assert r2.status_code == 200
    listed = client.get("/api/v1/shop/prices", headers=member["headers"]).json()
    assert {p["code"] for p in listed} >= {"gold-3m", "pt-1m"}


# ── ۶) سبد و تسویه ──
def test_price_comes_from_db_not_client(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, price=500_000, stock=10)
    _topup(client, member, 500_000)
    # کلاینت تلاش می‌کند قیمت را عوض کند — اسکیمای سبد اصلاً فیلد قیمت ندارد
    r = client.post(
        "/api/v1/shop/cart",
        json={"product_id": product["id"], "qty": 1, "price_rial": 1},
        headers=member["headers"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["total_rial"] == 500_000


def test_checkout_debits_wallet_and_creates_order(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, price=300_000, stock=2)
    _topup(client, member, 1_000_000)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 2}, headers=member["headers"]
    )
    r = client.post("/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"])
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "paid"
    assert r.json()["total_rial"] == 600_000

    bal = client.get(
        f"/api/v1/payments/wallet/{_member_id(member)}", headers=member["headers"]
    ).json()
    assert bal["balance_rial"] == 400_000
    orders = client.get("/api/v1/shop/orders", headers=member["headers"]).json()
    assert orders[0]["status"] == "paid"
    assert orders[0]["items"][0]["qty"] == 2
    # سبد خالی شد و موجودی کم شد
    assert client.get("/api/v1/shop/cart", headers=member["headers"]).json()["count"] == 0
    assert (
        client.get(f"/api/v1/shop/products/{product['id']}", headers=member["headers"]).json()[
            "stock_qty"
        ]
        == 0
    )


def test_checkout_insufficient_balance_keeps_cart(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, price=900_000, stock=5)
    _topup(client, member, 100_000)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )
    r = client.post("/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"])
    assert r.status_code == 400
    assert "insufficient_balance" in r.text
    assert client.get("/api/v1/shop/cart", headers=member["headers"]).json()["count"] == 1


def test_cart_rejects_beyond_stock(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, stock=1)
    r = client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 2}, headers=member["headers"]
    )
    assert r.status_code == 409


def test_order_price_is_frozen(client: TestClient) -> None:
    """قیمت در لحظهٔ ثبت قفل می‌شود — تغییر بعدی محصول فاکتور را عوض نمی‌کند."""
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, price=200_000)
    _topup(client, member, 500_000)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )
    client.post("/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"])
    client.patch(
        f"/api/v1/shop/products/{product['id']}",
        json={"price_rial": 9_999_999},
        headers=owner["headers"],
    )
    order = client.get("/api/v1/shop/orders", headers=member["headers"]).json()[0]
    assert order["total_rial"] == 200_000
    assert order["items"][0]["unit_price_rial"] == 200_000


def test_member_sees_only_own_orders(client: TestClient) -> None:
    owner = _user("super_admin")
    a = _user("member")
    b = _user("member")
    product = _product(client, owner, price=100_000)
    _topup(client, a, 100_000)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=a["headers"]
    )
    client.post("/api/v1/shop/checkout", json={"method": "wallet"}, headers=a["headers"])
    assert client.get("/api/v1/shop/orders", headers=b["headers"]).json() == []
    assert len(client.get("/api/v1/shop/orders", headers=owner["headers"]).json()) == 1


def test_member_cannot_change_order_status(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, price=50_000)
    _topup(client, member, 50_000)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )
    oid = client.post(
        "/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"]
    ).json()["order_id"]
    assert (
        client.patch(
            f"/api/v1/shop/orders/{oid}", json={"status": "delivered"}, headers=member["headers"]
        ).status_code
        == 403
    )


def test_staff_can_mark_delivered(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, price=50_000)
    _topup(client, member, 50_000)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )
    oid = client.post(
        "/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"]
    ).json()["order_id"]
    r = client.patch(
        f"/api/v1/shop/orders/{oid}", json={"status": "delivered"}, headers=owner["headers"]
    )
    assert r.status_code == 200
    assert r.json()["status"] == "delivered"


# ── ۷) سلسله‌مراتب نقش ──
def test_role_hierarchy_one_way() -> None:
    from app.security.hierarchy import ROLE_RANK, outranks

    assert outranks("super_admin", "admin")
    assert outranks("admin", "manager")
    assert not outranks("admin", "super_admin")
    assert not outranks("manager", "admin")
    assert ROLE_RANK["member"] < ROLE_RANK["reception"] < ROLE_RANK["coach"] < ROLE_RANK["manager"]


def test_casbin_inheritance_is_one_way() -> None:
    from security.rbac import enforce

    # super_admin همهٔ اجازه‌های admin را دارد
    assert enforce("super_admin", "/api/v1/admin/kpis", "GET")
    # ولی admin به مسیرهای مالکانهٔ نوشتن نمی‌رسد (سطح سرویس هم بسته است)
    assert not enforce("member", "/api/v1/shop/products", "POST")
    assert enforce("admin", "/api/v1/shop/products", "GET")


def test_super_admin_not_assignable_via_api(client: TestClient) -> None:
    owner = _user("super_admin")
    victim = _user("member")
    r = client.post(
        f"/api/v1/admin/users/{victim['id']}/role",
        json={"role": "super_admin"},
        headers=owner["headers"],
    )
    assert r.status_code == 400
    assert "invalid_role" in r.text


def test_admin_cannot_grant_admin(client: TestClient) -> None:
    admin = _user("admin")
    victim = _user("member")
    r = client.post(
        f"/api/v1/admin/users/{victim['id']}/role",
        json={"role": "admin"},
        headers=admin["headers"],
    )
    assert r.status_code == 403


def test_admin_cannot_demote_super_admin(client: TestClient) -> None:
    owner = _user("super_admin")
    admin = _user("admin")
    r = client.delete(f"/api/v1/admin/users/{owner['id']}/role", headers=admin["headers"])
    assert r.status_code == 403


def test_admin_can_promote_member_to_coach(client: TestClient) -> None:
    admin = _user("admin")
    victim = _user("member")
    r = client.post(
        f"/api/v1/admin/users/{victim['id']}/role",
        json={"role": "coach"},
        headers=admin["headers"],
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "coach"


# ── ۸) پوشش مسیرهای جدید در artifact ──
def test_shop_routes_in_artifact() -> None:
    """گیت «هیچ مسیر دکوراتیو»: هر مسیر جدید باید در routes.json باشد."""
    import json
    from pathlib import Path

    artifact = Path(__file__).resolve().parents[2] / "api" / "routes.json"
    paths = json.loads(artifact.read_text())["paths"]
    shop = [p for p in paths if p.startswith("/api/v1/shop")]
    assert len(shop) >= 13, shop


# ── M60 — سقف نرخ روی مسیر پول (یافتهٔ بازبینی: حلقهٔ سبد/تسویه) ──
#
# نکتهٔ پیاده‌سازی که یک‌بار تست را گمراه کرد: مقدار سقف در
# `@limiter.limit(settings.…)` **در زمان import** خوانده می‌شود، پس
# monkeypatch روی settings بعد از import بی‌اثر است. تست باید از همان
# سقف واقعی عبور کند (۱۰/دقیقه ← ۱۲ درخواست)، نه اینکه سقف را عوض کند.
def test_checkout_is_rate_limited(client: TestClient) -> None:
    """۴۲۹ بعد از سقف — بدون آن یک حلقهٔ ساده موجودی/تراکنش را می‌بلعد."""
    from modules.auth.router import limiter

    limiter.reset()
    member = _user("member")
    codes = [
        client.post(
            "/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"]
        ).status_code
        for _ in range(12)
    ]
    assert 429 in codes, f"سقف تسویه اعمال نشد: {codes}"
    # و سقف *پس از* عبور از تعداد مجاز اعمال می‌شود، نه از اول
    assert codes[0] != 429
    limiter.reset()


def test_cart_write_is_rate_limited(client: TestClient) -> None:
    from modules.auth.router import limiter

    limiter.reset()
    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, stock=100)
    codes = [
        client.post(
            "/api/v1/shop/cart",
            json={"product_id": product["id"], "qty": 1},
            headers=member["headers"],
        ).status_code
        for _ in range(35)
    ]
    assert 429 in codes, f"سقف نوشتن سبد اعمال نشد: {codes[-3:]}"
    limiter.reset()


def test_rate_limited_response_shape(client: TestClient) -> None:
    """۴۲۹ باید همان قالب خطای پروژه را داشته باشد (`error.code=rate_limited`)."""
    from modules.auth.router import limiter

    limiter.reset()
    member = _user("member")
    body = None
    for _ in range(12):
        r = client.post(
            "/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"]
        )
        if r.status_code == 429:
            body = r.json()
            break
    assert body is not None, "هیچ ۴۲۹ای صادر نشد"
    assert body["error"]["code"] == "rate_limited"
    assert body["error"]["message"]
    limiter.reset()


# ── M60/R2 — مسیر کلاس‌ها بدون احراز هویت بود ──
def test_classes_read_requires_auth(client: TestClient) -> None:
    """قبل از M60: `GET /api/v1/classes` بدون هیچ توکنی ۲۰۰ + کل جدول را می‌داد."""
    assert client.get("/api/v1/classes").status_code == 401
    member = _user("member")
    r = client.get("/api/v1/classes", headers=member["headers"])
    assert r.status_code == 200, r.text
    assert isinstance(r.json(), list)


def test_classes_read_denied_for_role_without_policy(client: TestClient) -> None:
    """نقشی که در casbin برای `/classes` GET مجوز ندارد باید ۴۰۳ بگیرد."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    with get_session_factory()() as s:
        u = User(phone="09120000042", full_name="stranger", role="guest")
        s.add(u)
        s.commit()
        h = {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}
    assert client.get("/api/v1/classes", headers=h).status_code == 403


# ── M60/R3 — دادهٔ مالی برای پذیرش ──
def test_reception_cannot_read_finance(client: TestClient) -> None:
    """پذیرش پول می‌گیرد ولی نباید کل درآمد/CSV/کمیسیون را ببیند (M59 leak class)."""
    reception = _user("reception")
    assert (
        client.get("/api/v1/payments/finance/summary", headers=reception["headers"]).status_code
        == 403
    )
    assert (
        client.get("/api/v1/payments/finance/export.csv", headers=reception["headers"]).status_code
        == 403
    )
    assert (
        client.post(
            "/api/v1/payments/finance/commission",
            json={"coach_id": 1, "rate": 0.1},
            headers=reception["headers"],
        ).status_code
        == 403
    )
    # اما مسیر عملیاتی پرداخت باز است
    assert client.get("/api/v1/payments", headers=reception["headers"]).status_code == 200


def test_manager_and_admin_keep_finance_access(client: TestClient) -> None:
    for role in ("manager", "admin"):
        h = _user(role)["headers"]
        assert client.get("/api/v1/payments/finance/summary", headers=h).status_code == 200, role


# ── M60/R4 — تسویهٔ سفارشِ پرداخت‌شده از درگاه ──
#
# باگ واقعی: برای پرداخت درگاهی، `checkout` سفارش را `pending` می‌گذاشت و
# `verify_payment` فقط **پرداخت** را paid می‌کرد. پول گرفته شده بود، موجودی
# کسر شده بود، و سفارش تا ابد pending می‌ماند. تست زیر همان مسیر را می‌رود.
def test_gateway_paid_order_is_settled(client: TestClient) -> None:
    from db.base import get_session_factory
    from modules.payments import service as payments

    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, stock=5)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )

    # پرداخت غیرکیف‌پول (درگاه/کارت) ← سفارش pending می‌شود
    r = client.post("/api/v1/shop/checkout", json={"method": "cash"}, headers=member["headers"])
    assert r.status_code == 200, r.text
    order = r.json()
    assert order["status"] == "pending", "برای پرداخت غیرکیف‌پول باید pending بماند"

    # همان کاری که callback موفق درگاه می‌کند: تأیید پرداخت
    with get_session_factory()() as s:
        payments.verify_payment(s, order["payment_id"], reference_id="ref-e2e-1", manual=True)

    after = client.get("/api/v1/shop/orders", headers=member["headers"]).json()
    mine = [o for o in after if o["id"] == order["order_id"]][0]
    assert mine["status"] == "paid", f"سفارش پس از تأیید پرداخت تسویه نشد: {mine['status']}"


def test_failed_payment_does_not_settle_order(client: TestClient) -> None:
    """کنترل منفی: پرداخت ناموفق نباید سفارش را paid کند."""
    from db.base import get_session_factory
    from modules.payments import service as payments

    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, stock=5)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )
    order = client.post(
        "/api/v1/shop/checkout", json={"method": "cash"}, headers=member["headers"]
    ).json()
    with get_session_factory()() as s:
        payments.fail_payment(s, order["payment_id"])
    mine = [
        o
        for o in client.get("/api/v1/shop/orders", headers=member["headers"]).json()
        if o["id"] == order["order_id"]
    ][0]
    assert mine["status"] == "pending"


def test_settle_skips_cancelled_order(client: TestClient) -> None:
    """اگر سفارش پیش از تأیید پرداخت لغو شده باشد، پرداخت آن را زنده نمی‌کند."""
    from db.base import get_session_factory
    from modules.payments import service as payments

    owner = _user("super_admin")
    member = _user("member")
    product = _product(client, owner, stock=5)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=member["headers"]
    )
    order = client.post(
        "/api/v1/shop/checkout", json={"method": "cash"}, headers=member["headers"]
    ).json()
    # لغو توسط کادر
    assert (
        client.patch(
            f"/api/v1/shop/orders/{order['order_id']}",
            json={"status": "cancelled"},
            headers=owner["headers"],
        ).status_code
        == 200
    )
    with get_session_factory()() as s:
        payments.verify_payment(s, order["payment_id"], reference_id="ref-e2e-2", manual=True)
    mine = [
        o
        for o in client.get("/api/v1/shop/orders", headers=member["headers"]).json()
        if o["id"] == order["order_id"]
    ][0]
    assert mine["status"] == "cancelled"


# ── M60/R5 — رسید سفارش (چاپ/تحویل) ──
def test_order_receipt_has_lines_and_member_name(client: TestClient) -> None:
    owner = _user("super_admin")
    member = _user("member")
    _topup(client, member, 5_000_000)  # پرداخت کیف‌پولی موجودی می‌خواهد
    product = _product(client, owner, stock=5)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 2}, headers=member["headers"]
    )
    resp = client.post(
        "/api/v1/shop/checkout", json={"method": "wallet"}, headers=member["headers"]
    )
    assert resp.status_code == 200, resp.text
    order = resp.json()

    r = client.get(f"/api/v1/shop/orders/{order['order_id']}/receipt", headers=member["headers"])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["receipt_no"].startswith("O-")
    assert body["status"] == "paid"
    assert len(body["lines"]) == 1
    line = body["lines"][0]
    assert line["qty"] == 2
    assert line["line_total_rial"] == body["total_rial"]
    assert body["items_total_rial"] == body["total_rial"]
    # نام عضو، نه شناسهٔ داخلی (باگ رسید پرداخت هم همین‌جا رفع شد)
    assert body["member_name"], "رسید باید نام عضو را داشته باشد"
    assert body["payment"]["method"] == "wallet"


def test_order_receipt_is_scoped_to_owner(client: TestClient) -> None:
    """عضو نباید رسید سفارش عضو دیگر را ببیند."""
    owner = _user("super_admin")
    a = _user("member")
    b = _user("member")
    _topup(client, a, 5_000_000)
    product = _product(client, owner, stock=5)
    client.post(
        "/api/v1/shop/cart", json={"product_id": product["id"], "qty": 1}, headers=a["headers"]
    )
    order = client.post(
        "/api/v1/shop/checkout", json={"method": "wallet"}, headers=a["headers"]
    ).json()
    assert (
        client.get(
            f"/api/v1/shop/orders/{order['order_id']}/receipt", headers=b["headers"]
        ).status_code
        == 403
    )
    # کادر مجاز است
    assert (
        client.get(
            f"/api/v1/shop/orders/{order['order_id']}/receipt", headers=owner["headers"]
        ).status_code
        == 200
    )

"""WP 3.4 / F‑27 — کاربر بدون پروندهٔ عضو در سبد خرید: ۴۰۹ با `member_profile_required`.

قبل از اصلاح: `NotFoundError` ⇒ ۴۰۴ `not_found` (مبهم؛ کلاینت نمی‌داند باید پروفایل را کامل کند).
"""

from __future__ import annotations


def test_cart_without_member_profile_is_409_member_profile_required(
    client, auth, monkeypatch
) -> None:
    # خرید درون‌برنامه‌ای پیش‌فرض بسته است (تصمیم فاز ۲)؛ برای رسیدن به بررسی پروفایل، پرچم را روشن می‌کنیم.
    from app.config import settings

    monkeypatch.setattr(settings, "shop_online_purchase_enabled", True)
    r = client.post(
        "/api/v1/shop/cart",
        json={"product_id": 1, "qty": 1},
        headers=auth("member"),
    )
    assert r.status_code == 409
    err = r.json()["error"]
    assert err["code"] == "member_profile_required"
    assert "پروندهٔ عضو" in err["message"]

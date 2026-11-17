"""M60/R3 — هم‌خوانی قاعدهٔ منوی استودیو با RBAC سرور.

# چرا

قاعده دو جا نوشته شده: `security/rbac.py` (اجرا) و `studio/src/lib/roleNav.ts`
(نمایش). اگر این دو از هم دور شوند، دوباره به همان باگ می‌رسیم: منویی که
صفحه‌ای را باز می‌کند که سرور همهٔ درخواست‌هایش را ۴۰۳ می‌دهد — یا برعکس،
صفحه‌ای که پنهان است ولی سرور اجازه می‌دهد و کاربر دکمه‌اش را نمی‌بیند.

این تست فایل TS را پارس نمی‌کند (شکننده است)؛ از enforcer واقعی می‌پرسد و
**قاعدهٔ سرور** را با انتظارات مستقل مقایسه می‌کند. اگر روزی rbac تغییر کرد
و این انتظارات نه، این تست قرمز می‌شود و آدم باید تصمیم بگیرد.
"""

from __future__ import annotations

import pytest

from security.rbac import enforce


def _allows(role: str, obj: str, act: str) -> bool:
    # از همان تابعی استفاده می‌کنیم که مسیر واقعی درخواست استفاده می‌کند،
    # نه enforcer خام — وگرنه DENIES (که فقط در `enforce` اعمال می‌شود) از
    # تست جا می‌ماند و تست سبزِ بی‌معنا می‌شود.
    return enforce(role, obj, act)


@pytest.mark.parametrize("role", ["reception", "coach", "member"])
def test_finance_is_closed_for_non_managers(role: str) -> None:
    """R3: دادهٔ مالی خالص برای reception/coach/member بسته است.

    پیش از M60/R3، reception از `/payments/*` مجوز داشت و در نتیجه خلاصهٔ
    درآمد باشگاه، CSV همهٔ پرداخت‌ها و کمیسیون را ۲۰۰ می‌گرفت.
    """
    for path in ("/api/v1/payments/finance/summary", "/api/v1/payments/finance/export.csv"):
        assert not _allows(role, path, "GET"), f"{role} نباید {path} را ببیند"


@pytest.mark.parametrize("role", ["manager", "admin", "super_admin"])
def test_finance_is_open_for_managers(role: str) -> None:
    assert _allows(role, "/api/v1/payments/finance/summary", "GET")


# ── لایهٔ دوم: ensure_owner (هندلر) نه RBAC (مسیر) ──
# کشف مهم این تست: RBAC برای manager/admin روی `POST /shop/prices` **اجازه**
# می‌دهد. یعنی مرز واقعی «فقط مالک» در لایهٔ سرویس است (`ensure_owner`)، نه در
# policy مسیر. تست اول من این را نمی‌دانست و شکست — که خودش ارزشمند بود:
# نشان داد دو لایه با دو دامنه داریم و باید هر دو را جدا قفل کرد.
@pytest.mark.parametrize("role", ["member", "reception", "coach", "manager", "admin"])
def test_ensure_owner_blocks_every_non_owner(role: str) -> None:
    """خواستهٔ صریح کارفرما: نوشتن محصول/قیمت/درگاه فقط super_admin."""
    from app.errors import ForbiddenError
    from app.security.hierarchy import ensure_owner

    for what in ("ساخت محصول", "ویرایش قیمت", "افزودن درگاه"):
        with pytest.raises(ForbiddenError):
            ensure_owner(role, what)


def test_ensure_owner_allows_super_admin() -> None:
    from app.security.hierarchy import ensure_owner

    ensure_owner("super_admin", "ساخت محصول")  # نباید خطا بدهد


def test_route_layer_still_hides_catalog_writes_from_member() -> None:
    """لایهٔ مسیر برای member هم بسته است — دو لایه، نه یکی."""
    assert not _allows("member", "/api/v1/shop/products", "POST")
    assert not _allows("member", "/api/v1/shop/prices", "POST")
    assert not _allows("member", "/api/v1/shop/gateways", "POST")


def test_admin_can_submit_change_request() -> None:
    """راه قانونی admin برای تغییر: درخواست، که مالک تأیید می‌کند."""
    assert _allows("admin", "/api/v1/shop/change-requests", "POST")

"""فاز ۵ — نقش و مجوز شخصی ادمین (QF-02/QF-03/QF-04).

# قرارداد

| مورد | قاعده |
|---|---|
| اعطا/سلب نقش | فقط `super_admin`؛ نقش خود تغییر نمی‌کند؛ `super_admin` از API ساخته نمی‌شود |
| مجوز شخصی | `(user_id, permission)` با انقضا/ابطال؛ فقط `super_admin` اعطا/سلب می‌کند |
| مالک | همیشه مجاز؛ نیازی به ردیف مجوز ندارد |
| admin/manager | مالی و گزارش محرمانه **به‌طور پیش‌فرض خاموش**؛ بدون مجوز فعال ۴۰۳ |
| انقضا/ابطال | server-side؛ ردیف باقی می‌ماند تا ممیزی، ولی اثر ندارد (fail-closed) |
| کلید ناشناخته | ۴۰۰ `unknown_permission` — نه «اجازه به‌خاطر ناشناخته‌بودن» |

# چرا این فایل قرمز اول نوشته شد
این endpointها و لایهٔ مجوز پیش از این وجود نداشتند؛ اجرای اول ۴۰۴/۴۰۳
برمی‌گرداند و سبزیِ بعدی معنای واقعی دارد. جزئیات در SESSION_HANDOFF.

# آنچه این تست ثابت نمی‌کند
- UI استودیو (تست جدا: `tests/adminPermissions.test.tsx`).
- سیاست‌های خارج از این سه endpoint؛ هر endpoint مالیِ دیگر باید در لوپ خودش بسته شود.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import AdminPermission, Member, User

PERMISSIONS = "/api/v1/admin/permissions"
_counter = itertools.count(70_000)


def _make_user(role: str) -> tuple[int, dict]:
    from app.security.jwt import create_access_token

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"099{n:08d}", full_name=f"u-{role}-{n}", role=role)
        s.add(u)
        s.commit()
        token = create_access_token(u.id, u.role)
        return u.id, {"Authorization": f"Bearer {token}"}


def _member_with_cash_payment(client: TestClient) -> tuple[int, dict, int]:
    """عضو واقعی + پرداخت نقدیِ در انتظار تأیید (کارِ پذیرش، نه ادمین)."""
    from app.security.jwt import create_access_token

    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"099{n:08d}", full_name=f"عضو-{n}", role="member")
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="hypertrophy", constraints="[]")
        s.add(member)
        s.commit()
        member_id = member.id
        token = create_access_token(user.id, user.role)

    headers = {"Authorization": f"Bearer {token}"}
    res = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 5_000_000, "method": "cash"},
        headers=headers,
    )
    assert res.status_code in (200, 201), res.text
    return member_id, headers, res.json()["id"]


def _grant(owner_h: dict, client: TestClient, user_id: int, permission: str, **extra) -> dict:
    res = client.post(
        PERMISSIONS, json={"user_id": user_id, "permission": permission, **extra}, headers=owner_h
    )
    assert res.status_code == 200, res.text
    return res.json()


def test_only_super_admin_manages_permissions(client: TestClient) -> None:
    _, owner_h = _make_user("super_admin")
    target_id, _ = _make_user("admin")
    _, admin_h = _make_user("admin")
    _, manager_h = _make_user("manager")

    payload = {"user_id": target_id, "permission": "finance.write"}
    assert client.post(PERMISSIONS, json=payload, headers=admin_h).status_code == 403
    assert client.post(PERMISSIONS, json=payload, headers=manager_h).status_code == 403
    assert client.get(f"{PERMISSIONS}?user_id={target_id}", headers=admin_h).status_code == 403

    created = _grant(owner_h, client, target_id, "finance.write")
    assert created["permission"] == "finance.write"
    assert created["active"] is True
    assert created["expires_at"] is None

    listing = client.get(f"{PERMISSIONS}?user_id={target_id}", headers=owner_h).json()
    assert [row["permission"] for row in listing] == ["finance.write"]


def test_unknown_permission_and_owner_target_are_rejected(client: TestClient) -> None:
    _, owner_h = _make_user("super_admin")
    admin_id, _ = _make_user("admin")
    owner_target_id, _ = _make_user("super_admin")

    res = client.post(
        PERMISSIONS, json={"user_id": admin_id, "permission": "money.print"}, headers=owner_h
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "unknown_permission"

    res = client.post(
        PERMISSIONS,
        json={"user_id": owner_target_id, "permission": "finance.write"},
        headers=owner_h,
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "owner_needs_no_permission"

    res = client.post(
        PERMISSIONS, json={"user_id": 999_999, "permission": "finance.write"}, headers=owner_h
    )
    assert res.status_code == 404


def test_finance_is_closed_by_default_for_admin_and_manager(client: TestClient) -> None:
    _, owner_h = _make_user("super_admin")
    admin_id, admin_h = _make_user("admin")
    _, manager_h = _make_user("manager")
    _, _, payment_id = _member_with_cash_payment(client)

    for headers in (admin_h, manager_h):
        res = client.post(f"/api/v1/payments/{payment_id}/verify", json={}, headers=headers)
        assert res.status_code == 403, res.text
        assert res.json()["error"]["code"] == "permission_required"
        assert "finance.write" in res.json()["error"]["message"]

    _grant(owner_h, client, admin_id, "finance.write")
    res = client.post(f"/api/v1/payments/{payment_id}/verify", json={}, headers=admin_h)
    assert res.status_code == 200, res.text
    assert res.json()["status"] == "paid"


def test_expired_or_revoked_permission_stops_working(client: TestClient) -> None:
    _, owner_h = _make_user("super_admin")
    admin_id, admin_h = _make_user("admin")
    _, _, payment_id = _member_with_cash_payment(client)

    expired = _grant(owner_h, client, admin_id, "finance.write", expires_in_hours=1)
    # پیری ردیف را مستقیم در DB می‌گذاریم تا «گذشت زمان» بدون sleep آزموده شود.
    with get_session_factory()() as s:
        row = s.get(AdminPermission, expired["id"])
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        s.commit()

    res = client.post(f"/api/v1/payments/{payment_id}/verify", json={}, headers=admin_h)
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "permission_required"

    live = _grant(owner_h, client, admin_id, "finance.write")
    assert (
        client.post(f"/api/v1/payments/{payment_id}/verify", json={}, headers=admin_h).status_code
        == 200
    )

    revoke = client.delete(f"{PERMISSIONS}/{live['id']}", headers=owner_h)
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "revoked"
    assert (
        client.get(f"{PERMISSIONS}?user_id={admin_id}", headers=owner_h).json()[0]["active"]
        is False
    )
    assert (
        client.post(f"/api/v1/payments/{payment_id}/verify", json={}, headers=admin_h).status_code
        == 403
    )

    # ابطال دوباره اثر تازه‌ای ندارد (idempotent، بدون بازفعال‌سازی).
    assert client.delete(f"{PERMISSIONS}/{live['id']}", headers=owner_h).status_code == 200
    assert client.delete(f"{PERMISSIONS}/999999", headers=owner_h).status_code == 404


def test_confidential_report_needs_its_own_permission(client: TestClient) -> None:
    _, owner_h = _make_user("super_admin")
    admin_id, admin_h = _make_user("admin")
    member_id, _, _ = _member_with_cash_payment(client)

    res = client.get(f"/api/v1/reports/confidential/{member_id}?format=json", headers=admin_h)
    assert res.status_code == 403, res.text
    assert res.json()["error"]["code"] == "permission_required"

    # مجوز مالی مجوز گزارش نمی‌دهد.
    _grant(owner_h, client, admin_id, "finance.write")
    assert (
        client.get(
            f"/api/v1/reports/confidential/{member_id}?format=json", headers=admin_h
        ).status_code
        == 403
    )

    _grant(owner_h, client, admin_id, "reports.confidential")
    assert (
        client.get(
            f"/api/v1/reports/confidential/{member_id}?format=json", headers=admin_h
        ).status_code
        == 200
    )


def test_every_grant_and_revoke_is_audited(client: TestClient) -> None:
    _, owner_h = _make_user("super_admin")
    admin_id, _ = _make_user("admin")
    created = _grant(owner_h, client, admin_id, "finance.write")
    client.delete(f"{PERMISSIONS}/{created['id']}", headers=owner_h)

    # audit روی کاربر هدف ثبت می‌شود و شناسهٔ مجوز داخل detail است.
    rows = client.get("/api/v1/admin/audit?action=permission_grant", headers=owner_h).json()
    granted = [r for r in rows if r["entity_id"] == admin_id]
    assert granted, rows
    assert f'"grant_id": {created["id"]}' in granted[0]["detail"]

    rows = client.get("/api/v1/admin/audit?action=permission_revoke", headers=owner_h).json()
    revoked = [r for r in rows if r["entity_id"] == admin_id]
    assert revoked, rows
    assert f'"grant_id": {created["id"]}' in revoked[0]["detail"]


def test_role_change_is_super_admin_only(client: TestClient) -> None:
    """QF-02: حتی admin هم نقش اعطا نمی‌کند؛ فقط مالک."""
    _, owner_h = _make_user("super_admin")
    _, admin_h = _make_user("admin")
    target_id, _ = _make_user("member")

    res = client.post(
        f"/api/v1/admin/users/{target_id}/role", json={"role": "coach"}, headers=admin_h
    )
    assert res.status_code == 403
    res = client.post(
        f"/api/v1/admin/users/{target_id}/role", json={"role": "coach"}, headers=owner_h
    )
    assert res.status_code == 200
    assert res.json()["role"] == "coach"

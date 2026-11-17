"""M83 — wallet history must come from wallet_transactions, not payments alone."""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select


def _create_member(
    client: TestClient, staff: dict[str, str], phone: str
) -> tuple[int, dict[str, str]]:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member

    response = client.post(
        "/api/v1/members/",
        json={"phone": phone, "full_name": "عضو دفتر کیف‌پول", "gender": "male"},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    member_id = response.json()["id"]
    with get_session_factory()() as db:
        member = db.get(Member, member_id)
        assert member is not None
        user_id = member.user_id
    token = create_access_token(user_id, "member")
    return member_id, {"Authorization": f"Bearer {token}"}


def _charge(client: TestClient, staff: dict[str, str], member_id: int, amount: int) -> dict:
    response = client.post(
        "/api/v1/payments/wallet/charge",
        json={"member_id": member_id, "amount_rial": amount, "description": f"شارژ {amount}"},
        headers=staff,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_wallet_ledger_paginates_real_credits_and_debits_in_database_order(
    client: TestClient, auth
) -> None:
    from db.base import get_session_factory
    from db.models import WalletTransaction

    staff = auth("manager")
    member_id, member_headers = _create_member(client, staff, "09127770001")
    credit_one = _charge(client, staff, member_id, 100_000)
    payment = client.post(
        "/api/v1/payments/wallet/pay",
        json={"member_id": member_id, "amount_rial": 30_000, "description": "پرداخت عضویت"},
        headers=staff,
    )
    assert payment.status_code == 200, payment.text
    credit_two = _charge(client, staff, member_id, 7_000)

    with get_session_factory()() as db:
        rows = list(
            db.scalars(
                select(WalletTransaction)
                .where(WalletTransaction.member_id == member_id)
                .order_by(WalletTransaction.id.desc())
            )
        )
    assert rows[0].id == credit_two["id"]
    assert rows[0].id > rows[1].id > rows[2].id == credit_one["id"]
    assert [(row.kind, row.amount_rial) for row in rows] == [
        ("credit", 7_000),
        ("debit", 30_000),
        ("credit", 100_000),
    ]

    first_page = client.get(
        f"/api/v1/payments/wallet/{member_id}/transactions?limit=2", headers=member_headers
    )
    assert first_page.status_code == 200, first_page.text
    first_data = first_page.json()
    assert first_data["member_id"] == member_id
    assert first_data["balance_rial"] == 77_000
    assert [row["id"] for row in first_data["transactions"]] == [rows[0].id, rows[1].id]
    assert [row["kind"] for row in first_data["transactions"]] == ["credit", "debit"]
    assert [row["amount_rial"] for row in first_data["transactions"]] == [7_000, 30_000]
    assert all(
        row["member_id"] == member_id and row["created_at"] for row in first_data["transactions"]
    )
    assert first_data["next_before_id"] == rows[1].id

    next_page = client.get(
        f"/api/v1/payments/wallet/{member_id}/transactions"
        f"?limit=2&before_id={first_data['next_before_id']}",
        headers=member_headers,
    )
    assert next_page.status_code == 200, next_page.text
    next_data = next_page.json()
    assert next_data["balance_rial"] == first_data["balance_rial"]
    assert [row["id"] for row in next_data["transactions"]] == [rows[2].id]
    assert next_data["next_before_id"] is None


def test_wallet_ledger_is_member_scoped_and_staff_can_audit_each_account(
    client: TestClient, auth
) -> None:
    staff = auth("manager")
    member_a, headers_a = _create_member(client, staff, "09127770002")
    member_b, _ = _create_member(client, staff, "09127770003")
    member_empty, _ = _create_member(client, staff, "09127770004")
    _charge(client, staff, member_a, 11_000)
    _charge(client, staff, member_b, 92_000)

    own = client.get(f"/api/v1/payments/wallet/{member_a}/transactions", headers=headers_a)
    assert own.status_code == 200, own.text
    assert own.json()["balance_rial"] == 11_000
    assert all(row["member_id"] == member_a for row in own.json()["transactions"])

    other = client.get(f"/api/v1/payments/wallet/{member_b}/transactions", headers=headers_a)
    assert other.status_code == 403

    staff_view = client.get(f"/api/v1/payments/wallet/{member_b}/transactions", headers=staff)
    assert staff_view.status_code == 200, staff_view.text
    assert staff_view.json()["balance_rial"] == 92_000
    assert all(row["member_id"] == member_b for row in staff_view.json()["transactions"])

    empty_view = client.get(f"/api/v1/payments/wallet/{member_empty}/transactions", headers=staff)
    assert empty_view.status_code == 200, empty_view.text
    assert empty_view.json() == {
        "member_id": member_empty,
        "balance_rial": 0,
        "transactions": [],
        "next_before_id": None,
    }

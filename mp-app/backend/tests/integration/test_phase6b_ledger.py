"""فاز ۶ لوپ ۲ — دفتر پول: رویداد، idempotency، معکوس‌سازی، تطبیق (QF-05).

# قرارداد

| مورد | قاعده |
|---|---|
| ثبت | هر حرکت کیف‌پول یک ردیف **فقط-افزودنی** در `ledger_entries` می‌سازد |
| علامت | مبلغ علامت‌دار است: شارژ +، پرداخت − |
| idempotency | کلید یکتا؛ تکرار همان کلید ردیف دوم نمی‌سازد، کلید با مبلغ متفاوت ۴۰۹ |
| معکوس‌سازی | ردیف جبرانی با علامت مخالف؛ ردیف اصلی `reversed_by` می‌گیرد |
| معکوس دوباره | ۴۰۱… نه: ۴۰۰ `already_reversed`؛ معکوسِ معکوس هم ممنوع |
| مجوز | معکوس‌سازی `finance.write` می‌خواهد؛ دیدن دفتر محدود به عضو خود/کادر |
| تطبیق | مجموع دفتر باید **برابر** موجودی کیف‌پول باشد (`reconcile`) |

# چرا این تست

پیش از این، پول کیف‌پول فقط از `wallet_transactions` محاسبه می‌شد: قابل خواندن
بود ولی **رویداد جبرانی، کلید idempotency و اثبات تطبیق نداشت**. یک شارژ
اشتباه فقط با حذف دستی ردیف اصلاح می‌شد — یعنی تاریخچه جعل‌پذیر بود.

# آنچه تست نمی‌کند
- انتقال واقعی پول بانکی (`BLOCKED`).
- دفتر دوطرفهٔ کامل حسابداری (بدهکار/بستانکار با حساب‌ها)؛ این‌جا دفتر رویدادِ
  عضو است، نه trial balance.
"""

from __future__ import annotations

import itertools

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import LedgerEntry, Member, User, WalletTransaction
from modules.payments.service import wallet_balance
from tests.integration._actors import create_actor

_counter = itertools.count(90_000)


def _member() -> tuple[int, dict]:
    from app.security.jwt import create_access_token

    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"094{n:08d}", full_name=f"عضو-دفتر-{n}", role="member")
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="hypertrophy", constraints="[]")
        s.add(member)
        s.commit()
        token = create_access_token(user.id, user.role)
        return member.id, {"Authorization": f"Bearer {token}"}


def _charge(client: TestClient, headers: dict, member_id: int, amount: int, key: str | None = None):
    body = {"member_id": member_id, "amount_rial": amount}
    if key:
        body["idempotency_key"] = key
    return client.post("/api/v1/payments/wallet/charge", json=body, headers=headers)


def test_wallet_charge_and_pay_write_signed_entries(client: TestClient) -> None:
    member_id, member_h = _member()
    staff_h = create_actor("manager", ["finance.write"])

    assert _charge(client, staff_h, member_id, 500_000).status_code == 200
    pay = client.post(
        "/api/v1/payments/wallet/pay",
        json={"member_id": member_id, "amount_rial": 120_000},
        headers=member_h,
    )
    assert pay.status_code == 200, pay.text

    ledger = client.get(f"/api/v1/payments/ledger/{member_id}", headers=staff_h)
    assert ledger.status_code == 200, ledger.text
    body = ledger.json()
    assert body["balance_rial"] == 380_000
    kinds = [(row["kind"], row["amount_rial"]) for row in body["entries"]]
    assert ("charge", 500_000) in kinds
    assert any(k == "pay" and a == -120_000 for k, a in kinds)
    # هیچ ردیفی حذف‌شدنی نیست: endpoint حذف وجود ندارد.
    assert client.delete(f"/api/v1/payments/ledger/{member_id}", headers=staff_h).status_code in (
        404,
        405,
    )


def test_ledger_balance_reconciles_with_wallet_balance(client: TestClient) -> None:
    member_id, member_h = _member()
    staff_h = create_actor("manager", ["finance.write"])
    _charge(client, staff_h, member_id, 300_000)
    client.post(
        "/api/v1/payments/wallet/pay",
        json={"member_id": member_id, "amount_rial": 50_000},
        headers=member_h,
    )

    with get_session_factory()() as s:
        wallet = wallet_balance(s, member_id)
        ledger_sum = sum(
            row.amount_rial
            for row in s.query(LedgerEntry).filter(LedgerEntry.member_id == member_id)
        )
    assert wallet == ledger_sum == 250_000


def test_duplicate_charge_key_does_not_double_credit(client: TestClient) -> None:
    member_id, _ = _member()
    staff_h = create_actor("manager", ["finance.write"])

    first = _charge(client, staff_h, member_id, 100_000, key="charge-abc-1")
    second = _charge(client, staff_h, member_id, 100_000, key="charge-abc-1")
    assert first.status_code == second.status_code == 200

    with get_session_factory()() as s:
        assert (
            s.query(WalletTransaction).filter(WalletTransaction.member_id == member_id).count() == 1
        )
        assert s.query(LedgerEntry).filter(LedgerEntry.member_id == member_id).count() == 1
    assert (
        client.get(f"/api/v1/payments/wallet/{member_id}", headers=staff_h).json()["balance_rial"]
        == 100_000
    )


def test_same_key_with_different_amount_is_a_conflict(client: TestClient) -> None:
    member_id, _ = _member()
    staff_h = create_actor("manager", ["finance.write"])
    _charge(client, staff_h, member_id, 100_000, key="charge-conflict-1")

    res = _charge(client, staff_h, member_id, 900_000, key="charge-conflict-1")
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "idempotency_conflict"


def test_reversal_creates_a_compensating_entry(client: TestClient) -> None:
    member_id, _ = _member()
    staff_h = create_actor("manager", ["finance.write"])
    _charge(client, staff_h, member_id, 400_000)

    entries = client.get(f"/api/v1/payments/ledger/{member_id}", headers=staff_h).json()["entries"]
    charge_id = next(row["id"] for row in entries if row["kind"] == "charge")

    res = client.post(
        f"/api/v1/payments/ledger/{charge_id}/reverse",
        json={"reason": "شارژ اشتباه پذیرش"},
        headers=staff_h,
    )
    assert res.status_code == 200, res.text
    assert res.json()["reversal_entry"]["amount_rial"] == -400_000

    after = client.get(f"/api/v1/payments/ledger/{member_id}", headers=staff_h).json()
    assert after["balance_rial"] == 0
    original = next(row for row in after["entries"] if row["id"] == charge_id)
    assert original["reversed_by_id"] == res.json()["reversal_entry"]["id"]
    # کیف‌پول هم برگشته است (ردیف debit جبرانی)، نه فقط دفتر.
    assert (
        client.get(f"/api/v1/payments/wallet/{member_id}", headers=staff_h).json()["balance_rial"]
        == 0
    )


def test_double_reversal_and_reversal_of_reversal_are_refused(client: TestClient) -> None:
    member_id, _ = _member()
    staff_h = create_actor("manager", ["finance.write"])
    _charge(client, staff_h, member_id, 200_000)
    entries = client.get(f"/api/v1/payments/ledger/{member_id}", headers=staff_h).json()["entries"]
    charge_id = entries[0]["id"]

    first = client.post(
        f"/api/v1/payments/ledger/{charge_id}/reverse", json={"reason": "خطا"}, headers=staff_h
    )
    assert first.status_code == 200
    second = client.post(
        f"/api/v1/payments/ledger/{charge_id}/reverse", json={"reason": "خطا"}, headers=staff_h
    )
    assert second.status_code == 400
    assert second.json()["error"]["code"] == "already_reversed"

    reversal_id = first.json()["reversal_entry"]["id"]
    on_reversal = client.post(
        f"/api/v1/payments/ledger/{reversal_id}/reverse", json={"reason": "دوباره"}, headers=staff_h
    )
    assert on_reversal.status_code == 400
    assert on_reversal.json()["error"]["code"] == "cannot_reverse_reversal"


def test_reversal_requires_finance_write_and_reason(client: TestClient) -> None:
    member_id, _ = _member()
    writer = create_actor("manager", ["finance.write"])
    reader = create_actor("manager")
    _charge(client, writer, member_id, 150_000)
    entry_id = client.get(f"/api/v1/payments/ledger/{member_id}", headers=writer).json()["entries"][
        0
    ]["id"]

    denied = client.post(
        f"/api/v1/payments/ledger/{entry_id}/reverse", json={"reason": "خطا"}, headers=reader
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "permission_required"

    no_reason = client.post(
        f"/api/v1/payments/ledger/{entry_id}/reverse", json={"reason": ""}, headers=writer
    )
    assert no_reason.status_code == 422

    missing = client.post(
        "/api/v1/payments/ledger/999999/reverse", json={"reason": "خطا"}, headers=writer
    )
    assert missing.status_code == 404


def test_member_sees_only_own_ledger(client: TestClient) -> None:
    mine_id, my_h = _member()
    other_id, _ = _member()
    staff_h = create_actor("manager", ["finance.write"])
    _charge(client, staff_h, mine_id, 10_000)
    _charge(client, staff_h, other_id, 20_000)

    own = client.get(f"/api/v1/payments/ledger/{mine_id}", headers=my_h)
    assert own.status_code == 200
    assert own.json()["balance_rial"] == 10_000

    foreign = client.get(f"/api/v1/payments/ledger/{other_id}", headers=my_h)
    assert foreign.status_code in (403, 404)


def test_every_reversal_is_audited(client: TestClient) -> None:
    member_id, _ = _member()
    staff_h = create_actor("manager", ["finance.write"])
    owner_h = create_actor("super_admin")
    _charge(client, staff_h, member_id, 75_000)
    entry_id = client.get(f"/api/v1/payments/ledger/{member_id}", headers=staff_h).json()[
        "entries"
    ][0]["id"]
    client.post(
        f"/api/v1/payments/ledger/{entry_id}/reverse",
        json={"reason": "فیش تکراری"},
        headers=staff_h,
    )
    rows = client.get("/api/v1/admin/audit?action=ledger_reversal", headers=owner_h).json()
    assert any(r["entity_id"] == entry_id for r in rows), rows

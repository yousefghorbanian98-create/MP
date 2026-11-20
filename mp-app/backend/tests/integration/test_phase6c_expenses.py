"""فاز ۶ لوپ ۳ — هزینهٔ خارجی: ثبت، دوره، اصلاح با دلیل، audit (QF-06).

# قرارداد

| مورد | قاعده |
|---|---|
| ثبت | مبلغ ریال صحیح مثبت، دسته، تاریخ هزینه، طرف‌حساب اختیاری، توضیح |
| دوره | `GET /expenses?from=&to=` فقط همان بازه را جمع می‌زند و به تفکیک دسته می‌دهد |
| اصلاح | هر ویرایش **دلیل** می‌خواهد و یک ردیف تاریخچه با مقدار قبل/بعد می‌سازد |
| حذف | نرم است: از جمع‌ها بیرون می‌رود، تاریخچه و audit می‌مانند |
| مجوز | ثبت/اصلاح/حذف `finance.write`؛ خواندن `finance.read` — جدا از هم |
| audit | `expense_created` / `expense_updated` / `expense_deleted` با actor |

# چرا این تست

پیش از این، هزینه‌های باشگاه (اجاره، حقوق، تجهیزات) در سیستم **جایی نداشتند**؛
تنها پول ورودی گزارش می‌شد. هر محاسبهٔ سود/زیان یا باید دستی بود یا دروغ.

# آنچه تست نمی‌کند
- فایل فیش خصوصی هزینه (`qf-06` در فاز بعد؛ آپلود فیش فعلاً فقط برای پرداخت است).
- گزارش سود/زیان دوره‌ای کامل با بازگشت‌ها (QF-10).
"""

from __future__ import annotations

import itertools
from datetime import date, timedelta

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import AuditLog, Expense, ExpenseRevision
from tests.integration._actors import create_actor

_counter = itertools.count(70_000)


def _day(offset: int = 0) -> str:
    return (date(2026, 3, 15) + timedelta(days=offset)).isoformat()


def _create(client: TestClient, headers: dict, **overrides):
    body = {
        "amount_rial": 12_000_000,
        "category": "rent",
        "spent_on": _day(0),
        "payee": "مالک ساختمان",
        "note": "اجارهٔ فروردین",
    }
    body.update(overrides)
    return client.post("/api/v1/expenses", json=body, headers=headers)


def _period(client: TestClient, headers: dict, start: str, end: str, **params):
    return client.get(
        "/api/v1/expenses",
        params={"from": start, "to": end, **params},
        headers=headers,
    )


def test_expense_create_requires_finance_write_grant(client: TestClient) -> None:
    no_grant = create_actor("manager")
    reader = create_actor("manager", ["finance.read"])

    assert _create(client, no_grant).status_code == 403
    assert _create(client, no_grant).json()["error"]["code"] == "permission_required"
    assert _create(client, reader).status_code == 403
    # خواندن برای دارندهٔ finance.read مجاز است ولی نوشتن نه — دو اختیار جدا.
    assert _period(client, reader, _day(-5), _day(5)).status_code == 200


def test_period_totals_only_include_expenses_in_range(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write", "finance.read"])

    rent = _create(client, staff, amount_rial=12_000_000, category="rent", spent_on=_day(0))
    salary = _create(client, staff, amount_rial=30_000_000, category="salary", spent_on=_day(1))
    outside = _create(client, staff, amount_rial=7_000_000, category="rent", spent_on=_day(40))
    assert rent.status_code == salary.status_code == outside.status_code == 200

    res = _period(client, staff, _day(0), _day(2))
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total_rial"] == 42_000_000
    assert body["count"] == 2
    by_category = {row["category"]: row["total_rial"] for row in body["by_category"]}
    assert by_category == {"rent": 12_000_000, "salary": 30_000_000}
    assert {row["id"] for row in body["items"]} == {rent.json()["id"], salary.json()["id"]}


def test_negative_or_zero_amount_is_rejected(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write"])
    assert _create(client, staff, amount_rial=0).status_code == 422
    assert _create(client, staff, amount_rial=-5_000).status_code == 422
    # مبلغ زیر یک‌هزار ریال = خطای ورود داده، نه گرد کردن خاموش.
    assert _create(client, staff, amount_rial=999).status_code == 422


def test_unknown_category_is_rejected(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write"])
    assert _create(client, staff, category="فضایی").status_code == 422


def test_update_requires_reason_and_keeps_revision_history(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write", "finance.read"])
    created = _create(client, staff, amount_rial=12_000_000).json()

    missing_reason = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"amount_rial": 13_000_000},
        headers=staff,
    )
    assert missing_reason.status_code == 422

    fixed = client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"amount_rial": 13_000_000, "reason": "افزایش اجارهٔ امسال"},
        headers=staff,
    )
    assert fixed.status_code == 200, fixed.text
    assert fixed.json()["amount_rial"] == 13_000_000

    with get_session_factory()() as s:
        revisions = (
            s.query(ExpenseRevision).filter(ExpenseRevision.expense_id == created["id"]).all()
        )
    assert len(revisions) == 1
    assert revisions[0].reason == "افزایش اجارهٔ امسال"
    assert '"from":12000000' in revisions[0].changes.replace(" ", "")
    assert '"to":13000000' in revisions[0].changes.replace(" ", "")

    period = _period(client, staff, _day(0), _day(2)).json()
    assert period["total_rial"] == 13_000_000  # جمع بعد از اصلاح، نه جمع تاریخچه


def test_soft_delete_leaves_totals_but_keeps_history_and_audit(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write", "finance.read"])
    created = _create(client, staff, amount_rial=5_000_000).json()

    deleted = client.request(
        "DELETE",
        f"/api/v1/expenses/{created['id']}",
        json={"reason": "دوبار ثبت شده بود"},
        headers=staff,
    )
    assert deleted.status_code == 200, deleted.text
    assert _period(client, staff, _day(0), _day(2)).json()["total_rial"] == 0

    with get_session_factory()() as s:
        row = s.get(Expense, created["id"])
        assert row is not None and row.deleted_at is not None
        actions = {a.action for a in s.query(AuditLog).filter(AuditLog.entity_id == created["id"])}
    assert {"expense_created", "expense_deleted"} <= actions


def test_create_and_update_are_audited_with_actor(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write"])
    created = _create(client, staff).json()
    client.patch(
        f"/api/v1/expenses/{created['id']}",
        json={"note": "به‌روزشده", "reason": "توضیح دقیق‌تر"},
        headers=staff,
    )

    with get_session_factory()() as s:
        rows = (
            s.query(AuditLog)
            .filter(AuditLog.entity_type == "expense", AuditLog.entity_id == created["id"])
            .all()
        )
    assert [r.action for r in rows] == ["expense_created", "expense_updated"]
    assert all(r.actor_user_id for r in rows)


def test_delete_requires_reason_and_write_grant(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write"])
    reader = create_actor("manager", ["finance.read"])
    created = _create(client, staff).json()

    no_reason = client.request(
        "DELETE", f"/api/v1/expenses/{created['id']}", json={}, headers=staff
    )
    assert no_reason.status_code == 422
    assert (
        client.request(
            "DELETE",
            f"/api/v1/expenses/{created['id']}",
            json={"reason": "اشتباه"},
            headers=reader,
        ).status_code
        == 403
    )
    assert (
        client.request(
            "DELETE",
            f"/api/v1/expenses/{created['id']}",
            json={"reason": "اشتباه"},
            headers=staff,
        ).status_code
        == 200
    )
    # حذف دوباره همان ردیف ← ۴۰۰، نه ۲۰۰ تکراری.
    again = client.request(
        "DELETE",
        f"/api/v1/expenses/{created['id']}",
        json={"reason": "اشتباه"},
        headers=staff,
    )
    assert again.status_code == 400
    assert again.json()["error"]["code"] == "expense_already_deleted"


def test_period_rejects_inverted_range_and_missing_expense(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write", "finance.read"])
    inverted = _period(client, staff, _day(5), _day(1))
    assert inverted.status_code == 400
    assert inverted.json()["error"]["code"] == "invalid_period"

    assert (
        client.patch(
            "/api/v1/expenses/99999999",
            json={"note": "x", "reason": "دلیل"},
            headers=staff,
        ).status_code
        == 404
    )

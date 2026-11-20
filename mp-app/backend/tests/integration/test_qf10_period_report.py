"""QF-10 — گزارش سود/زیان دوره‌ای با بازگشت‌ها (فاز ۶).

# قرارداد

| مورد | قاعده |
|---|---|
| دوره | هفته (شنبه‌ها) / ماه / سال به تقویم جلالی `Asia/Tehran` |
| بازگشت | در سبد روز `refunded_at` می‌افتد، نه `paid_at` |
| هزینه | فقط ردیف‌های زنده (`deleted_at IS NULL`) با `spent_on` در بازه |
| داده ناقص | بازگشت بدون تاریخ → `complete=false`، نه صفر |
| مجوز | `finance.read`؛ بدون آن ۴۰۳ |

# آنچه تست نمی‌کند
- خروجی بانک واقعی؛ پرداخت‌ها با ردیف دیتابیس ساخته می‌شوند.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import Expense, Member, Payment, User
from modules.reports import period as period_mod
from tests.integration._actors import create_actor


def _seed_member(s) -> int:
    u = User(phone="09990000010", full_name="qf10-member", role="member")
    s.add(u)
    s.flush()
    m = Member(user_id=u.id)
    s.add(m)
    s.flush()
    return m.id


def _pay(s, member_id: int, amount: int, paid_at: datetime, status: str = "paid") -> Payment:
    p = Payment(
        member_id=member_id,
        amount_rial=amount,
        method="cash",
        status=status,
        paid_at=paid_at if status != "pending" else None,
        description="qf10",
    )
    s.add(p)
    s.flush()
    return p


def test_month_is_jalali_tehran_window_not_gregorian() -> None:
    # دی ۱۴۰۵ (ماه ۱۰) = ۲۲ دسامبر ۲۰۲۶ تا ۲۰ ژانویه ۲۰۲۷ (end غیرشامل = ۲۱ ژانویه)
    w = period_mod.window_for("month", date(2026, 12, 25))
    assert w.start == date(2026, 12, 22)
    assert w.end == date(2027, 1, 21)
    assert w.label == "1405/10"


def test_nowruz_starts_the_year_and_week_starts_saturday() -> None:
    year = period_mod.window_for("year", date(2026, 4, 1))
    assert year.start == date(2026, 3, 21)
    assert year.end == date(2027, 3, 21)
    week = period_mod.window_for("week", date(2026, 11, 19))  # پنجشنبه
    assert week.start == date(2026, 11, 14)  # شنبه
    assert (week.end - week.start).days == 7


def test_unknown_kind_is_rejected() -> None:
    try:
        period_mod.window_for("quarter", date(2026, 1, 1))
    except Exception as exc:  # noqa: BLE001 - قرارداد: ApiError با کد
        assert getattr(exc, "code", "") == "invalid_period_kind"
    else:  # pragma: no cover
        raise AssertionError("دورهٔ ناشناخته باید رد شود")


def test_report_sums_by_hand_with_refund_in_its_own_day(client: TestClient) -> None:
    """جمع دستی: درآمد ۳۰۰، بازگشت ۱۰۰ (در دورهٔ دیگری)، هزینه ۵۰ و یک هزینهٔ حذف‌شده."""
    staff = create_actor("manager", ["finance.read"])
    # ماه ۱۴۰۵/۰۸ = ۲۳ اکتبر تا ۲۱ نوامبر ۲۰۲۶ (به وقت تهران)
    inside = datetime(2026, 10, 25, 9, 0, tzinfo=UTC)
    refund_in = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)
    # پرداختی که در ماه قبل آمده و در همین ماه برگشت خورده
    prev_month = datetime(2026, 9, 28, 9, 0, tzinfo=UTC)

    with get_session_factory()() as s:
        mid = _seed_member(s)
        _pay(s, mid, 200, inside)
        _pay(s, mid, 100, inside)
        old = _pay(s, mid, 100, prev_month, status="refunded")
        old.refunded_at = refund_in  # بازگشت در این ماه
        s.add(
            Expense(amount_rial=50, category="rent", spent_on=date(2026, 11, 1), payee="x", note="")
        )
        s.add(
            Expense(
                amount_rial=999,
                category="rent",
                spent_on=date(2026, 11, 1),
                payee="x",
                note="",
                deleted_at=datetime(2026, 11, 2, tzinfo=UTC),
            )
        )
        s.commit()

    res = client.get(
        "/api/v1/finance/reports/period",
        params={"kind": "month", "anchor": "2026-11-03"},
        headers=staff,
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["label"] == "1405/08"
    assert body["received_rial"] == 300
    assert body["refunds_rial"] == 100
    assert body["net_income_rial"] == 200
    assert body["expenses_rial"] == 50
    assert body["profit_rial"] == 150
    assert body["complete"] is True


def test_undated_refund_marks_report_incomplete_not_zero(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.read"])
    with get_session_factory()() as s:
        mid = _seed_member(s)
        _pay(s, mid, 500, datetime(2026, 10, 26, 9, 0, tzinfo=UTC), status="refunded")
        s.commit()
    body = client.get(
        "/api/v1/finance/reports/period",
        params={"kind": "month", "anchor": "2026-10-26"},
        headers=staff,
    ).json()
    assert body["undated_refunds_count"] >= 1
    assert body["complete"] is False


def test_period_requires_finance_read(client: TestClient) -> None:
    none = create_actor("manager")
    writer_only = create_actor("manager", ["finance.write"])
    assert client.get("/api/v1/finance/reports/period", headers=none).status_code == 403
    assert client.get("/api/v1/finance/reports/period", headers=writer_only).status_code == 403


def test_bad_anchor_is_400_invalid_date(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.read"])
    res = client.get("/api/v1/finance/reports/period", params={"anchor": "nope"}, headers=staff)
    assert res.status_code == 400, res.text
    assert res.json()["error"]["code"] == "invalid_date"

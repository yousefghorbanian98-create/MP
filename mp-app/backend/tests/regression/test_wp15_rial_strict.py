"""WP 1.5 (F‑09) — پول بزرگ و coercion رشته→عدد.

قبل از اصلاح: `2**53`، `2**53+1`، `10**18`، رشتهٔ «1000»، اعشار `1000.0` و `True` در
فیلدهای مبلغ پذیرفته می‌شدند؛ کمیسیون مربی با float محاسبه می‌شد (نتیجهٔ دقیق نبود).
بعد از اصلاح: نوع `Rial` (StrictInt، ≤ 2**53-1)؛ کمیسیون با Decimal و گرد به پایین.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from modules.expenses.schemas import ExpenseCreate
from modules.membership.schemas import MembershipCreate
from modules.payments.finance import coach_commission
from modules.payments.schemas import PaymentCreate, WalletCharge

UNSAFE = [2**53, 2**53 + 1, 10**18]
COERCED = ["1000", 1000.0, True, "1e6"]


def _field_rejected(factory, field: str) -> bool:
    try:
        factory()
    except ValidationError as exc:
        return any(err["loc"] and err["loc"][0] == field for err in exc.errors())
    return False


CASES = [
    ("payment", "amount_rial", lambda v: PaymentCreate(member_id=1, amount_rial=v)),
    (
        "expense",
        "amount_rial",
        lambda v: ExpenseCreate(amount_rial=v, category="other", spent_on=date(2026, 1, 1)),
    ),
    (
        "membership",
        "price_rial",
        lambda v: MembershipCreate(member_id=1, plan_name="ماهانه", duration_days=30, price_rial=v),
    ),
    ("wallet", "amount_rial", lambda v: WalletCharge(member_id=1, amount_rial=v)),
]


@pytest.mark.parametrize(("name", "field", "make"), CASES, ids=[c[0] for c in CASES])
@pytest.mark.parametrize("value", UNSAFE + COERCED, ids=repr)
def test_money_field_rejects_unsafe_and_coerced(name, field, make, value) -> None:
    """F‑09: عدد ناامن یا رشته/اعشار/bool باید خطای اعتبارسنجی بدهد."""
    assert _field_rejected(lambda: make(value), field)


@pytest.mark.parametrize(("name", "field", "make"), CASES, ids=[c[0] for c in CASES])
def test_money_field_accepts_plain_int_and_max_safe(name, field, make) -> None:
    """حد بالا دقیقاً 2**53-1 است و عدد صحیح معمولی پذیرفته می‌شود."""
    assert not _field_rejected(lambda: make(2000), field)
    assert not _field_rejected(lambda: make(2**53 - 1), field)


def test_commission_is_exact_for_large_totals() -> None:
    """کمیسیون با float خطا دارد؛ با Decimal و گرد به پایین دقیق است."""

    class _FakeDB:
        def get(self, _model, _id):
            return SimpleNamespace(full_name="مربی")

        def execute(self, _stmt):
            return SimpleNamespace(scalar=lambda: 10**18 + 7)

    result = coach_commission(_FakeDB(), coach_id=1, rate=0.3)
    expected = int(
        (Decimal(10**18 + 7) * Decimal(str(0.3))).to_integral_value(rounding="ROUND_FLOOR")
    )
    assert expected == 300000000000000002
    assert result["commission_rial"] == expected

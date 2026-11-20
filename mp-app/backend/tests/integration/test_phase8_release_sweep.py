"""فاز ۸ لوپ آخر — جاروی انتشار: یک جریان پول از مجوز تا گزارش (QF-32).

# چه چیزی را ثابت می‌کند

حلقه‌های قبلی هرکدام جدا سبزند؛ این تست **در کنار هم**:

1. مجوز شخصی: مدیر بدون `finance.write` رد می‌شود، پس از اعطای مالک می‌تواند.
2. دفتر پول: شارژ کیف‌پول + پرداخت نقدی → موجودی و `reconcile` منطبق.
3. هزینه: اجارهٔ همان روز ثبت می‌شود و در جمع دوره می‌آید.
4. گزارش روزانه: `net = پرداخت‌های موفق − هزینه‌ها` و اعداد از همان ردیف‌های واقعی.
5. نگهداری: پیش‌نمایش روی دادهٔ تازه صفر است و اجرا هیچ پولی را حذف نمی‌کند.
6. معکوس‌سازی دفتر: موجودی صفر می‌شود، دفتر همچنان با کیف‌پول منطبق است و
   گزارشِ ثبت‌شده دست‌نخورده می‌ماند (گزارش snapshot روز است، نه recalc).

# چرا این «جارو» است نه یک تست دیگر

پذیرش نهایی وقتی معنا دارد که این مسیرها در **یک نسخه** و با **یک تراکنش
واقعی** با هم کار کنند. تست‌های ایزوله می‌توانند همه سبز باشند در حالی که
ترکیبشان عدد غلط بدهد.

# آنچه همچنان `BLOCKED` است

انتقال واقعی بانکی، دستگاه اندروید، امضای release، PostgreSQL/backup در
استقرار و آزمایش ابری — هیچ‌کدام در این تست ادعا نمی‌شوند.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import Expense, LedgerEntry, Member, Payment, User
from modules.payments import ledger as ledger_service
from modules.payments.service import wallet_balance
from modules.reports import schedule as report_schedule
from tests.integration._actors import create_actor

_counter = itertools.count(60_000)


def _member() -> int:
    n = next(_counter)
    with get_session_factory()() as s:
        user = User(phone=f"095{n:08d}", full_name=f"عضو-جارو-{n}", role="member")
        s.add(user)
        s.commit()
        member = Member(user_id=user.id, goal="strength", constraints="[]")
        s.add(member)
        s.commit()
        return member.id


def _grant(client: TestClient, owner: dict, manager: dict, permission: str) -> None:
    import jwt as pyjwt

    from app.config import settings

    token = manager["Authorization"].split(" ", 1)[1]
    claims = pyjwt.decode(token, settings.secret_key, algorithms=["HS256"])
    res = client.post(
        "/api/v1/admin/permissions",
        json={"user_id": claims["sub"], "permission": permission, "expires_in_hours": 2},
        headers=owner,
    )
    assert res.status_code == 200, res.text


def test_money_flow_permission_ledger_expense_report_retention(client: TestClient) -> None:
    owner = create_actor("super_admin", ["finance.write", "finance.read"])
    manager = create_actor("manager")
    member_id = _member()
    today = report_schedule.tehran_date(datetime.now(UTC))

    # ۱) پیش از مجوز: هر نوشتن مالی ۴۰۳
    blocked = client.post(
        "/api/v1/payments/wallet/charge",
        json={"member_id": member_id, "amount_rial": 500_000},
        headers=manager,
    )
    assert blocked.status_code == 403
    assert blocked.json()["error"]["code"] == "permission_required"

    # اعطای مجوز توسط مالک (QF-03) — نه تغییر نقش، نه دست‌کاری دیتابیس
    _grant(client, owner, manager, "finance.write")
    _grant(client, owner, manager, "finance.read")

    # ۲) شارژ کیف‌پول → ردیف دفتر
    charged = client.post(
        "/api/v1/payments/wallet/charge",
        json={"member_id": member_id, "amount_rial": 500_000, "idempotency_key": "sweep-charge-1"},
        headers=manager,
    )
    assert charged.status_code == 200, charged.text

    # پرداخت نقدی موفق (بدون درگاه) — از مسیر واقعی API و تأیید مدیر
    payment = client.post(
        "/api/v1/payments",
        json={"member_id": member_id, "amount_rial": 300_000, "method": "cash"},
        headers=owner,
    )
    assert payment.status_code == 200, payment.text
    payment_id = payment.json()["id"]
    paid = client.post(f"/api/v1/payments/{payment_id}/verify", json={}, headers=owner)
    # تأیید نقدی با مسیر واقعی API (manual=True فقط برای نقدی/کارت‌خوان)
    assert paid.status_code == 200, paid.text
    assert paid.json()["status"] == "paid"

    # ۳) هزینهٔ همان روز (اجاره)
    expense = client.post(
        "/api/v1/expenses",
        json={
            "amount_rial": 200_000,
            "category": "rent",
            "spent_on": today.isoformat(),
            "payee": "مالک ساختمان",
            "note": "اجارهٔ روز جارو",
        },
        headers=manager,
    )
    assert expense.status_code == 200, expense.text

    # ۴) گزارش روزانه: net = موفق − هزینه
    report = client.post(
        "/api/v1/finance/reports/schedule/daily_finance/run", json={}, headers=owner
    )
    assert report.status_code == 200, report.text
    detail = client.get(f"/api/v1/finance/reports/daily/{today.isoformat()}", headers=owner)
    assert detail.status_code == 200, detail.text
    numbers = detail.json()
    assert numbers["expenses_total_rial"] == 200_000
    assert numbers["payments_total_rial"] >= 300_000
    assert numbers["net_rial"] == numbers["payments_total_rial"] - numbers["expenses_total_rial"]

    # ۵) دفتر و کیف‌پول منطبق
    with get_session_factory()() as s:
        wallet = wallet_balance(s, member_id)
        ledger_sum = sum(
            r.amount_rial for r in s.query(LedgerEntry).filter(LedgerEntry.member_id == member_id)
        )
        reconcile = ledger_service.reconcile(s, member_id)
    assert wallet == ledger_sum == 500_000
    assert reconcile["matches"] is True

    # ۶) نگهداری: دادهٔ تازه حذف نمی‌شود
    preview = client.get("/api/v1/admin/retention", headers=owner).json()
    assert preview["policies"]["audit_logs"]["expired"] == 0
    ran = client.post("/api/v1/admin/retention/run", json={}, headers=owner).json()
    assert ran["deleted"]["audit_logs"] == 0
    with get_session_factory()() as s:
        assert s.query(Expense).count() >= 1
        assert s.query(Payment).filter(Payment.id == payment_id).count() == 1

    # ۷) معکوس‌سازی دفتر: موجودی صفر، گزارش ثبت‌شده دست‌نخورده
    entry_id = next(
        r["id"]
        for r in client.get(f"/api/v1/payments/ledger/{member_id}", headers=manager).json()[
            "entries"
        ]
        if r["kind"] == "charge"
    )
    reversed_res = client.post(
        f"/api/v1/payments/ledger/{entry_id}/reverse",
        json={"reason": "شارژ آزمایشی جارو"},
        headers=manager,
    )
    assert reversed_res.status_code == 200, reversed_res.text
    after = client.get(f"/api/v1/payments/ledger/{member_id}", headers=manager).json()
    assert after["balance_rial"] == 0
    assert after["reconcile"]["matches"] is True
    assert (
        client.get(f"/api/v1/finance/reports/daily/{today.isoformat()}", headers=owner).json()[
            "net_rial"
        ]
        == numbers["net_rial"]
    ), "گزارش روز یک snapshot است؛ معکوس بعدی آن را بازنویسی نمی‌کند"

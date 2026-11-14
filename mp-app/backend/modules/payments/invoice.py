"""رسید و فاکتور (M16) — خروجی قطعی و قابل‌استناد."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from db.models import Member, Payment, WalletTransaction


def build_receipt(db: Session, payment_id: int) -> dict:
    """رسید پرداخت — برای نمایش/چاپ (US-303)."""
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    member = db.get(Member, payment.member_id)
    return {
        "receipt_no": f"R-{payment.id:06d}",
        "payment_id": payment.id,
        "member_name": member.user_id if member else None,
        "amount_rial": payment.amount_rial,
        "method": payment.method,
        "status": payment.status,
        "reference_id": payment.reference_id,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "issued_at": datetime.now(UTC).isoformat(),
        "branch": "Muscle Paradise",
    }


def build_invoice(db: Session, member_id: int, from_date: datetime | None = None) -> dict:
    """فاکتور تجمعی عضو — مجموع پرداخت‌ها + کیف‌پول (US-403)."""
    from sqlalchemy import select

    member = db.get(Member, member_id)
    if member is None:
        raise NotFoundError("عضو یافت نشد")
    payments = db.scalars(
        select(Payment).where(Payment.member_id == member_id, Payment.status == "paid")
    ).all()
    wallet_rows = db.scalars(
        select(WalletTransaction).where(WalletTransaction.member_id == member_id)
    ).all()
    total_paid = sum(p.amount_rial for p in payments)
    wallet_credit = sum(t.amount_rial for t in wallet_rows if t.kind == "credit")
    wallet_debit = sum(t.amount_rial for t in wallet_rows if t.kind == "debit")
    return {
        "invoice_no": f"INV-{member_id:05d}-{datetime.now(UTC):%Y%m}",
        "member_id": member_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "payments": [
            {
                "payment_id": p.id,
                "amount_rial": p.amount_rial,
                "method": p.method,
                "reference_id": p.reference_id,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
            }
            for p in payments
        ],
        "total_paid_rial": total_paid,
        "wallet_credit_rial": wallet_credit,
        "wallet_debit_rial": wallet_debit,
        "wallet_balance_rial": wallet_credit - wallet_debit,
        "due_rial": 0,  # بدهی در مدل فعلی وجود ندارد (M17: اقساط)
    }

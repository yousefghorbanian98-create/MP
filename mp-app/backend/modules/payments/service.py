"""سرویس payments — پرداخت و کیف‌پول."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, NotFoundError
from db.models import Member, Payment, WalletTransaction


def create_payment(
    db: Session,
    member_id: int,
    amount_rial: int,
    method: str = "zarinpal",
    description: str = "",
) -> Payment:
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    payment = Payment(
        member_id=member_id,
        amount_rial=amount_rial,
        method=method,
        description=description,
        branch_id=1,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def verify_payment(db: Session, payment_id: int, reference_id: str = "") -> Payment:
    """تأیید پرداخت (callback درگاه یا تأیید پذیرش). فقط pending قابل تأیید است."""
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    payment.status = "paid"
    payment.paid_at = datetime.now(UTC)
    payment.reference_id = reference_id or f"ref-{secrets.token_hex(6)}"
    db.commit()
    db.refresh(payment)
    from modules.admin.service import audit

    audit(db, None, "payment_verified", "payment", payment.id, {"amount_rial": payment.amount_rial})
    return payment


def fail_payment(db: Session, payment_id: int) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    payment.status = "failed"
    db.commit()
    db.refresh(payment)
    from modules.admin.service import audit

    audit(db, None, "payment_failed", "payment", payment.id, {})
    return payment


def list_payments(
    db: Session, member_id: int | None = None, status: str | None = None, user=None
) -> list[Payment]:
    if user is not None and user.role == "member":
        from app.security.ownership import get_own_member

        own = get_own_member(db, user)
        member_id = own.id if own else -1
    stmt = select(Payment).order_by(Payment.id.desc())
    if member_id is not None:
        stmt = stmt.where(Payment.member_id == member_id)
    if status is not None:
        stmt = stmt.where(Payment.status == status)
    return list(db.scalars(stmt))


def wallet_charge(
    db: Session, member_id: int, amount_rial: int, description: str = ""
) -> WalletTransaction:
    if amount_rial <= 0:
        raise ApiError("مبلغ شارژ باید مثبت باشد")
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    tx = WalletTransaction(
        member_id=member_id, amount_rial=amount_rial, kind="credit", description=description
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def wallet_balance(db: Session, member_id: int, user=None) -> int:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    """موجودی = مجموع credit − مجموع debit (مبالغ همیشه مثبت ذخیره می‌شوند)."""
    rows = db.scalars(select(WalletTransaction).where(WalletTransaction.member_id == member_id))
    return sum(t.amount_rial if t.kind == "credit" else -t.amount_rial for t in rows)


def wallet_pay(
    db: Session, member_id: int, amount_rial: int, description: str = "", user=None
) -> Payment:
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    """پرداخت از کیف‌پول — اتمیک: بررسی موجودی + بدهکاری + پرداخت paid در یک تراکنش."""
    if amount_rial <= 0:
        raise ApiError("مبلغ پرداخت باید مثبت باشد")
    if db.get(Member, member_id) is None:
        raise NotFoundError("عضو یافت نشد")
    balance = wallet_balance(db, member_id)
    if balance < amount_rial:
        raise ApiError("موجودی کیف‌پول کافی نیست", code="insufficient_balance")
    tx = WalletTransaction(
        member_id=member_id,
        amount_rial=amount_rial,
        kind="debit",
        description=description or "پرداخت از کیف‌پول",
    )
    db.add(tx)
    db.flush()
    payment = Payment(
        member_id=member_id,
        amount_rial=amount_rial,
        method="wallet",
        description=description,
        status="paid",
        paid_at=datetime.now(UTC),
        reference_id=f"wallet-{secrets.token_hex(6)}",
        branch_id=1,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    from modules.admin.service import audit

    audit(db, None, "wallet_spent", "payment", payment.id, {"amount_rial": amount_rial})
    return payment

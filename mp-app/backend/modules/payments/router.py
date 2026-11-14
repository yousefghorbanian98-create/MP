"""روتر payments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import DbSession, require_permission
from modules.payments import service
from modules.payments.schemas import (
    PaymentCreate,
    PaymentOut,
    PaymentVerify,
    WalletBalanceOut,
    WalletCharge,
    WalletTxOut,
)

router = APIRouter(
    prefix="/payments", tags=["payments"], dependencies=[Depends(require_permission())]
)


@router.post("", response_model=PaymentOut, summary="ایجاد پرداخت (US-302)")
def create_payment(payload: PaymentCreate, db: DbSession):
    return service.create_payment(
        db, payload.member_id, payload.amount_rial, payload.method, payload.description
    )


@router.post("/{payment_id}/verify", response_model=PaymentOut, summary="تأیید پرداخت")
def verify_payment(payment_id: int, payload: PaymentVerify, db: DbSession):
    return service.verify_payment(db, payment_id, payload.reference_id)


@router.post("/{payment_id}/fail", response_model=PaymentOut, summary="ناموفق‌شدن پرداخت")
def fail_payment(payment_id: int, db: DbSession):
    return service.fail_payment(db, payment_id)


@router.get("", response_model=list[PaymentOut], summary="لیست پرداخت‌ها (US-403)")
def list_payments(
    db: DbSession,
    member_id: int | None = Query(None),
    status: str | None = Query(None, pattern="^(pending|paid|failed)$"),
):
    return service.list_payments(db, member_id=member_id, status=status)


@router.post("/wallet/charge", response_model=WalletTxOut, summary="شارژ کیف‌پول")
def wallet_charge(payload: WalletCharge, db: DbSession):
    return service.wallet_charge(db, payload.member_id, payload.amount_rial, payload.description)


@router.post("/wallet/pay", response_model=PaymentOut, summary="پرداخت از کیف‌پول (M16)")
def wallet_pay(payload: WalletCharge, db: DbSession):
    return service.wallet_pay(db, payload.member_id, payload.amount_rial, payload.description)


@router.get("/invoice/{member_id}", summary="فاکتور تجمعی عضو (US-403 — M16)")
def invoice(member_id: int, db: DbSession):
    from modules.payments.invoice import build_invoice

    return build_invoice(db, member_id)


@router.get("/{payment_id}/receipt", summary="رسید پرداخت (US-303 — M16)")
def receipt(payment_id: int, db: DbSession):
    from modules.payments.invoice import build_receipt

    return build_receipt(db, payment_id)


@router.get(
    "/wallet/{member_id}", response_model=WalletBalanceOut, summary="موجودی کیف‌پول (US-103)"
)
def wallet_balance(member_id: int, db: DbSession):
    return {"member_id": member_id, "balance_rial": service.wallet_balance(db, member_id)}

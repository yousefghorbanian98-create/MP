"""روتر payments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import CurrentUser, DbSession, require_permission
from modules.payments import service
from modules.payments.schemas import (
    GatewayCallbackIn,
    PaymentCreate,
    PaymentOut,
    PaymentStartIn,
    PaymentStartOut,
    PaymentVerify,
    WalletBalanceOut,
    WalletCharge,
    WalletTxOut,
)

router = APIRouter(
    prefix="/payments", tags=["payments"], dependencies=[Depends(require_permission())]
)


@router.post("", response_model=PaymentOut, summary="ایجاد پرداخت (US-302)")
def create_payment(payload: PaymentCreate, db: DbSession, user: CurrentUser):
    return service.create_payment(
        db,
        payload.member_id,
        payload.amount_rial,
        payload.method,
        payload.description,
        user=user,
    )


@router.post(
    "/{payment_id}/start",
    response_model=PaymentStartOut,
    summary="آغاز پرداخت درگاه (authority + redirect) — Q6",
)
def start_payment(payment_id: int, payload: PaymentStartIn, db: DbSession):
    return service.start_payment(db, payment_id, payload.callback_url)


@router.post(
    "/{payment_id}/callback",
    response_model=PaymentOut,
    summary="callback درگاه — تأیید با authority و امضای مبلغ",
)
def gateway_callback(payment_id: int, payload: GatewayCallbackIn, db: DbSession):
    return service.verify_with_gateway(
        db, payment_id, authority=payload.authority, callback_token=payload.callback_token
    )


@router.post(
    "/{payment_id}/verify",
    response_model=PaymentOut,
    summary="تأیید دستی پرداخت نقدی/کارت‌خوان (پذیرش)",
)
def verify_payment(payment_id: int, payload: PaymentVerify, db: DbSession):
    # manual=True فقط برای نقدی و کارت‌خوان؛ پرداخت درگاهی مسیر امضاشده دارد.
    return service.verify_payment(db, payment_id, payload.reference_id, manual=True)


@router.post("/{payment_id}/fail", response_model=PaymentOut, summary="ناموفق‌شدن پرداخت")
def fail_payment(payment_id: int, db: DbSession):
    return service.fail_payment(db, payment_id)


@router.get("", response_model=list[PaymentOut], summary="لیست پرداخت‌ها (US-403)")
def list_payments(
    user: CurrentUser,
    db: DbSession,
    member_id: int | None = Query(None),
    status: str | None = Query(None, pattern="^(pending|paid|failed)$"),
):
    return service.list_payments(db, member_id=member_id, status=status, user=user)


@router.post("/wallet/charge", response_model=WalletTxOut, summary="شارژ کیف‌پول")
def wallet_charge(payload: WalletCharge, db: DbSession):
    return service.wallet_charge(db, payload.member_id, payload.amount_rial, payload.description)


@router.post("/wallet/pay", response_model=PaymentOut, summary="پرداخت از کیف‌پول (M16)")
def wallet_pay(payload: WalletCharge, db: DbSession, user: CurrentUser):
    return service.wallet_pay(
        db, payload.member_id, payload.amount_rial, payload.description, user=user
    )


@router.get("/invoice/{member_id}", summary="فاکتور تجمعی عضو (US-403 — M16)")
def invoice(member_id: int, db: DbSession, user: CurrentUser):
    from modules.payments.invoice import build_invoice

    return build_invoice(db, member_id, user=user)


@router.get("/{payment_id}/receipt", summary="رسید پرداخت (US-303 — M16)")
def receipt(payment_id: int, db: DbSession, user: CurrentUser):
    from modules.payments.invoice import build_receipt

    return build_receipt(db, payment_id, user=user)


@router.get(
    "/wallet/{member_id}", response_model=WalletBalanceOut, summary="موجودی کیف‌پول (US-103)"
)
def wallet_balance(member_id: int, db: DbSession, user: CurrentUser):
    return {
        "member_id": member_id,
        "balance_rial": service.wallet_balance(db, member_id, user=user),
    }


# ── M27: گزارش مالی، CSV، کمیسیون مربی (فقط admin/manager) ──
from fastapi.responses import PlainTextResponse  # noqa: E402

from modules.payments.finance import coach_commission, finance_summary, payments_csv  # noqa: E402


@router.get("/finance/summary", summary="خلاصهٔ مالی (M27)")
def _finance_summary(db: DbSession):
    return finance_summary(db)


@router.get(
    "/finance/export.csv", summary="خروجی CSV پرداخت‌ها (حسابداری)", response_class=PlainTextResponse
)
def _finance_csv(db: DbSession):
    return PlainTextResponse(payments_csv(db), media_type="text/csv; charset=utf-8")


class CommissionIn(BaseModel):
    coach_id: int
    rate: float | None = None


@router.post("/finance/commission", summary="کمیسیون مربی (M27)")
def _commission(payload: CommissionIn, db: DbSession):
    return coach_commission(db, payload.coach_id, payload.rate)

"""روتر payments."""

from __future__ import annotations

import html as _html

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from app.deps import CurrentUser, DbSession, require_permission
from app.errors import ApiError
from app.ids import MAX_SAFE_ID, Id
from modules.auth.router import limiter
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
    WalletLedgerOut,
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


@router.post(
    "/{payment_id}/refund",
    response_model=PaymentOut,
    summary="بازگشت وجه از درگاه (M110)",
)
def refund_payment_endpoint(payment_id: int, db: DbSession):
    return service.refund_payment(db, payment_id)


@router.get("", response_model=list[PaymentOut], summary="لیست پرداخت‌ها (US-403)")
def list_payments(
    user: CurrentUser,
    db: DbSession,
    member_id: int | None = Query(None, ge=1, le=MAX_SAFE_ID),
    status: str | None = Query(None, pattern="^(pending|paid|failed|refunded)$"),
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


# مالکیت داخل build_invoice ← ensure_member_scope(db, user, member_id)
# بررسی می‌شود (user به سرویس پاس می‌شود).
@router.get(  # nosemgrep: mp-member-path-without-ownership
    "/invoice/{member_id}", summary="فاکتور تجمعی عضو (US-403 — M16)"
)
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
def wallet_balance(member_id: Id, db: DbSession, user: CurrentUser):
    return {
        "member_id": member_id,
        "balance_rial": service.wallet_balance(db, member_id, user=user),
    }


@router.get(
    "/wallet/{member_id}/transactions",
    response_model=WalletLedgerOut,
    summary="دفتر گردش کیف‌پول عضو با صفحه‌بندی",
)
def wallet_transactions(
    member_id: Id,
    db: DbSession,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
    before_id: int | None = Query(None, ge=1, le=MAX_SAFE_ID),
):
    return service.wallet_ledger(db, member_id, user=user, limit=limit, before_id=before_id)


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
    coach_id: Id
    rate: float | None = Field(default=None, ge=0, le=100)


@router.post("/finance/commission", summary="کمیسیون مربی (M27)")
def _commission(payload: CommissionIn, db: DbSession):
    return coach_commission(db, payload.coach_id, payload.rate)


# ── بازگشت مرورگر از بانک (M110) ───────────────────────────────────────────────
# تنها مسیرِ *عمومیِ* payments. عمومی بودنش عمداً و اجباری است: بانکِ واقعی کاربر
# را با یک GET ساده — بدون session، بدون سرِ دستگاه — به `callback_url` برمی‌گرداند.
# نبودِ این مسیر یعنی چرخهٔ پرداخت فقط از راه deep-linkِ اپ بسته می‌شود و هیچ انسان
# ی با مرورگر نمی‌تواند آن را آزمود (دقیقاً همان کاری که بانک صندباکسِ محلی می‌کند).
# اعتبار از سه چیز می‌آید، نه از احراز هویت:
#   ۱) `token` — HMACِ خودِ ما روی (payment_id, مبلغ)؛ بدون آن مبلغ قابل جعل است؛
#   ۲) `Authority` — باید با `gateway_authority` ثبت‌شده در DB هم‌خوان باشد؛
#   ۳) verifyِ **یک‌بارمصرف** نزد بانک — پولی که بانک تأییدش نکرده پرداخت نمی‌شود.
# پس یک مهاجم با جعل فقط «صفحهٔ خطا» می‌گیرد؛ «پرداخت» نه.
# مسیر کامل برای شاهدِ گیت استودیو: /api/v1/payments/{payment_id}/gateway-return
return_router = APIRouter(prefix="/payments", tags=["payments"])
payments_return_router = return_router  # نامِ صریح برای api/v1/api.py


def _return_page(ok: bool, title: str, note: str) -> HTMLResponse:
    color = "#0a7d38" if ok else "#b00020"
    body = (
        "<!doctype html><html dir=rtl lang=fa><meta charset=utf-8>"
        "<style>body{font-family:system-ui;max-width:480px;margin:4rem auto;padding:0 1rem;"
        "text-align:center}h1{color:" + color + "}p{color:#555}"
        "code{background:#f4f4f4;padding:.1rem .3rem;border-radius:4px}</style>"
        f"<h1>{_html.escape(title)}</h1><p>{_html.escape(note)}</p>"
        "<p>می‌توانید به اپ برگردید.</p></html>"
    )
    return HTMLResponse(body)


@return_router.get("/{payment_id}/gateway-return", summary="بازگشت مرورگر از درگاه (M110)")
@limiter.limit("30/minute")
def gateway_return(
    request: Request,
    payment_id: int,
    db: DbSession,
    bank_authority: str = Query("", alias="Authority", max_length=80),
    token: str = Query("", max_length=80),
):
    # `Authority` با حرف بزرگ نامِ قراردادِ بانک است؛ `alias` همان را نگه می‌دارد
    # و openapi هم همان را نشان می‌دهد — فقط پایتون pep8 می‌ماند.
    try:
        payment = service.verify_with_gateway(
            db, payment_id, authority=bank_authority, callback_token=token
        )
    except ApiError as exc:
        if exc.code == "already_processed":
            # تازگی‌اش همین است: replayِ همین redirect (رفرشِ مرورگر) نباید خطا بدهد،
            # چون پول واقعاً پرداخت شده — و verifyِ بانک هم یک‌بارمصرفی را تضمین می‌کند.
            return _return_page(
                True, "پرداخت قبلاً ثبت شده", "نگران نباشید؛ این تراکنش یک بار بیشتر ثبت نمی‌شود."
            )
        return _return_page(False, "پرداخت تأیید نشد", str(exc))
    return _return_page(
        True, "پرداخت تأیید شد", f"مبلغ {payment.amount_rial:,} ریال نزد بانک تأیید و ثبت شد."
    )

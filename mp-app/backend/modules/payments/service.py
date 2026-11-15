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
    user=None,
) -> Payment:
    from app.security.ownership import ensure_member_scope

    # G8/D-005 — عضو فقط برای خودش؛ کادر برای هر عضو. بدون این، هر عضوی
    # می‌توانست برای هر عضو دیگری تراکنش بسازد.
    ensure_member_scope(db, user, member_id)
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


def verify_payment(
    db: Session, payment_id: int, reference_id: str = "", *, manual: bool = False
) -> Payment:
    """تأیید پرداخت (callback درگاه یا تأیید پذیرش). فقط pending قابل تأیید است.

    `manual=True` فقط برای نقدی/کارت‌خوان در پذیرش مجاز است: برای پرداخت
    درگاهی، تأیید بدون پاسخ امضاشدهٔ درگاه یعنی هر کسی با توکن می‌توانست
    پرداخت را «پرداخت‌شده» کند (یافتهٔ semgrep).
    """
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    # `manual` یعنی «انسان در پذیرش دیده است» — فقط برای نقدی/کارت‌خوان.
    # برای درگاه، حتی با manual هم باید پاسخ امضاشده وجود داشته باشد.
    if payment.method in ("zarinpal", "wallet") and (not manual or not payment.gateway_authority):
        raise ApiError(
            "پرداخت درگاهی فقط از callback امضاشدهٔ درگاه تأیید می‌شود",
            code="gateway_verification_required",
        )
    payment.status = "paid"
    payment.paid_at = datetime.now(UTC)
    payment.reference_id = reference_id or f"ref-{secrets.token_hex(6)}"
    db.commit()
    db.refresh(payment)
    from modules.admin.service import audit

    audit(db, None, "payment_verified", "payment", payment.id, {"amount_rial": payment.amount_rial})
    return payment


def start_payment(db: Session, payment_id: int, callback_url: str = "") -> dict:
    """آغاز پرداخت درگاه — authority از درگاه واقعی، نه از ورودی کاربر.

    پیش از این `gateway.py` (Mock + زرین‌پال + امضای HMAC) کامل نوشته شده
    بود ولی **هیچ مصرف‌کننده‌ای نداشت**: پرداخت همیشه pending می‌شد و
    verify با هر reference_id دلخواه «پرداخت‌شده» اعلام می‌کرد.
    """
    from modules.payments.gateway import PaymentGatewayError, get_gateway, signed_token

    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    if payment.method == "wallet":
        raise ApiError("پرداخت کیف‌پول مسیر درگاه ندارد", code="wallet_not_gateway")
    if payment.gateway_authority:
        # اگر دو بار authority صادر شود، کدام تراکنش واقعی است؟ هیچ‌کدام معلوم نیست.
        raise ApiError("این پرداخت قبلاً در درگاه آغاز شده است", code="already_started")

    gw = get_gateway()
    try:
        started = gw.start(payment.amount_rial, payment.description or "", callback_url)
    except PaymentGatewayError as exc:
        raise ApiError(str(exc), code=exc.code) from exc

    payment.gateway_authority = started.authority
    db.commit()
    db.refresh(payment)
    from modules.admin.service import audit

    audit(db, None, "payment_started", "payment", payment.id, {"amount_rial": payment.amount_rial})
    return {
        "payment_id": payment.id,
        "authority": started.authority,
        "redirect_url": started.redirect_url,
        "amount_rial": payment.amount_rial,
        # امضای HMAC تا callback نتواند مبلغ را عوض کند (G8-مالی)
        "callback_token": signed_token(payment.id, payment.amount_rial),
    }


def verify_with_gateway(
    db: Session, payment_id: int, authority: str = "", callback_token: str = ""
) -> Payment:
    """تأیید واقعی: authority باید همان باشد که درگاه صادر کرده، و مبلغ هم‌خوان."""
    from modules.payments.gateway import PaymentGatewayError, get_gateway, verify_token

    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    if not payment.gateway_authority:
        raise ApiError("این پرداخت هنوز در درگاه آغاز نشده است", code="not_started")
    if callback_token and not verify_token(payment_id, payment.amount_rial, callback_token):
        raise ApiError(
            "امضای callback نامعتبر است — مبلغ یا شناسه دست‌کاری شده", code="bad_signature"
        )
    if authority and authority != payment.gateway_authority:
        raise ApiError("authority با تراکنش آغازشده هم‌خوان نیست", code="authority_mismatch")

    gw = get_gateway()
    try:
        result = gw.verify(payment.gateway_authority, payment.amount_rial)
    except PaymentGatewayError as exc:
        raise ApiError(str(exc), code=exc.code) from exc
    if not result.ok:
        raise ApiError("درگاه تأیید نکرد", code="gateway_rejected")
    # manual=True فقط برای گذر از بررسیِ «مسیر دستی»؛ خودِ پاسخ درگاه
    # همین لحظه و با امضا دریافت شد و authority در DB ثبت است.
    return verify_payment(db, payment_id, reference_id=result.reference_id, manual=True)


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

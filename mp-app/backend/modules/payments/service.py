"""سرویس payments — پرداخت و کیف‌پول."""

from __future__ import annotations

import secrets
from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, aliased

from app.config import settings
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
    # M60/R4 — تسویهٔ سفارشِ فروشگاه در همان تراکنش
    _settle_shop_order(db, payment.id)
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

    # امضای HMAC تا callback نتواند مبلغ را عوض کند (G8-مالی)
    token = signed_token(payment.id, payment.amount_rial)
    if not callback_url:
        # اگر کلاینت جایی نسازد (مثلاً پرداخت از پنل پذیرش، یا آزمون دستیِ بانک
        # صندباکس)، بازگشتِ مرورگر به مسیر عمومی gateway-return می‌افتد. بانک‌های
        # واقعی query را به همین نشانی **اضافه** می‌کنند، پس token در مسیر می‌ماند.
        callback_url = (
            f"{settings.public_base_url.rstrip('/')}/api/v1/payments/"
            f"{payment.id}/gateway-return?token={token}"
        )

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
        "callback_token": token,
    }


def verify_with_gateway(
    db: Session,
    payment_id: int,
    authority: str = "",
    callback_token: str = "",
    require_token: bool = False,
) -> Payment:
    """تأیید واقعی: authority باید همان باشد که درگاه صادر کرده، و مبلغ هم‌خوان.

    `require_token`: مسیر عمومیِ بازگشتِ مرورگر **نباید** با توکنِ خالی رد شود؛
    نبودِ آن یعنی «امضا اختیاری است» — روی مسیر بدون-لاگین این درست نیست. مسیر
    داخلیِ POST /callback که توکن را از خودِ پاسخ start می‌گیرد همان سخت‌گیری را
    دارد و نیازِ به پرچم ندارد، ولی عمداً یکسان رفتار می‌کنیم.
    """
    from modules.payments.gateway import PaymentGatewayError, get_gateway, verify_token

    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status != "pending":
        raise ApiError("این پرداخت قبلاً پردازش شده است", code="already_processed")
    if not payment.gateway_authority:
        raise ApiError("این پرداخت هنوز در درگاه آغاز نشده است", code="not_started")
    if require_token and not callback_token:
        raise ApiError("توکن بازگشت نبود — تسویه نمی‌شود", code="missing_token")
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


def _settle_shop_order(db: Session, payment_id: int) -> None:
    """سفارش فروشگاهِ وصل به این پرداخت را «پرداخت‌شده» کن.

    # باگ واقعی (M60/R4)

    `shop.checkout` برای پرداخت درگاهی سفارش را `pending` می‌گذاشت و
    `payment_id` را ثبت می‌کرد. وقتی callback درگاه موفق می‌شد،
    `verify_payment` فقط **پرداخت** را paid می‌کرد؛ هیچ‌کس سراغ سفارش نمی‌رفت.
    نتیجه: پول گرفته شده بود، موجودی کسر شده بود، و سفارش تا ابد `pending`
    می‌ماند — نه به انبار می‌رفت، نه لغو می‌شد. (با TestClient تأیید شد:
    callback ۲۰۰ و `orders.status` همچنان `pending`.)

    جای این منطق در لایهٔ پرداخت است چون تنها نقطه‌ای است که «پول واقعاً
    رسید» را می‌داند؛ گذاشتنش در روتِر درگاه یعنی هر مسیر تأیید آینده دوباره
    فراموشش می‌کند.
    """
    # import داخل تابع: `modules.shop.service` خودش payments را import می‌کند ←
    # حلقهٔ import در بارگذاری ماژول.
    from db.models import Order

    order = db.scalar(select(Order).where(Order.payment_id == payment_id))
    if order is None or order.status == "paid":
        return
    if order.status != "pending":
        # مثلاً لغو شده — پرداخت را برنمی‌گردانیم؛ فقط ثبت می‌کنیم تا در
        # ممیزی/گزارش دیده شود (بازپرداخت خارج از دامنهٔ این تغییر است).
        from modules.admin.service import audit

        audit(
            db,
            None,
            "order_paid_but_not_pending",
            "order",
            order.id,
            {"order_status": order.status, "payment_id": payment_id},
        )
        return
    order.status = "paid"
    from modules.admin.service import audit

    audit(db, None, "order_settled_by_payment", "order", order.id, {"payment_id": payment_id})


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


def refund_payment(db: Session, payment_id: int) -> Payment:
    """بازگشت وجه از درگاه (M110) — فقط پرداخت درگاهیِ تأییدشده، و فقط یک بار.

    سه تصمیم که عمداً گرفته شده:

    ۱) مرجع بازگشت در ستون مستقل ثبت می‌شود و مرجع پرداخت اصلی تغییر نمی‌کند.
    ۲) وضعیت `refunded` است نه `failed`: «پرداخت شد و بعد برگشت» با «پرداخت نشد» یکی
       نیست — گزارش مالی باید درآمد را کم کند، نه اینکه تراکنش را از تاریخچه بردارد.
    ۳) اگر بانک بگوید «قبلاً برگشت خورده» (code 254)، وضعیت را می‌گذاریم `refunded` و
       خطا نمی‌دهیم: حالتِ واگرا بدتر از تکرارِ بی‌ضرر است (idempotency).
    """
    from modules.payments.gateway import PaymentGatewayError, get_gateway

    payment = db.get(Payment, payment_id)
    if payment is None:
        raise NotFoundError("پرداخت یافت نشد")
    if payment.status == "refunded":
        raise ApiError("این پرداخت قبلاً برگشت خورده است", code="already_refunded")
    if payment.status != "paid":
        raise ApiError("فقط پرداخت تأییدشده قابل بازگشت است", code="not_refundable")
    if not payment.gateway_authority:
        raise ApiError("این پرداخت مسیر درگاه ندارد", code="wallet_not_gateway")

    gw = get_gateway()
    refund = getattr(gw, "refund", None)
    if refund is None:
        raise ApiError("درگاه فعلی بازگشت وجه را پشتیبانی نمی‌کند", code="refund_unsupported")
    try:
        result = refund(payment.gateway_authority, payment.amount_rial)
    except PaymentGatewayError as exc:
        raise ApiError(str(exc), code=exc.code) from exc
    if not result.ok and not result.already:
        raise ApiError("درگاه بازگشت را تأیید نکرد", code="refund_rejected")

    payment.status = "refunded"
    payment.refund_reference = result.reference_id or None
    db.commit()
    db.refresh(payment)
    from modules.admin.service import audit

    audit(
        db,
        None,
        "payment_refunded",
        "payment",
        payment.id,
        {
            "amount_rial": payment.amount_rial,
            "refund_ref": result.reference_id,
            "already": result.already,
        },
    )
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


def _wallet_balance_expr(member_id: int):
    """Database-side credit − debit aggregate shared by wallet reads."""
    signed_amount = case(
        (WalletTransaction.kind == "credit", WalletTransaction.amount_rial),
        else_=-WalletTransaction.amount_rial,
    )
    return (
        select(func.coalesce(func.sum(signed_amount), 0))
        .where(WalletTransaction.member_id == member_id)
        .scalar_subquery()
    )


def wallet_balance(db: Session, member_id: int, user=None) -> int:
    """موجودی = مجموع credit − مجموع debit (مبالغ همیشه مثبت ذخیره می‌شوند)."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    return int(db.scalar(select(_wallet_balance_expr(member_id))) or 0)


def wallet_ledger(
    db: Session,
    member_id: int,
    *,
    user=None,
    limit: int = 50,
    before_id: int | None = None,
) -> dict:
    """Return the member-scoped credit/debit ledger, newest first, with a stable cursor."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
    page_stmt = select(WalletTransaction).where(WalletTransaction.member_id == member_id)
    if before_id is not None:
        page_stmt = page_stmt.where(WalletTransaction.id < before_id)
    page_rows = page_stmt.order_by(WalletTransaction.id.desc()).limit(limit + 1).subquery()
    page_transaction = aliased(WalletTransaction, page_rows)
    balance = _wallet_balance_expr(member_id)
    rows = db.execute(
        select(Member.id, balance.label("balance_rial"), page_transaction)
        .outerjoin(page_transaction, page_transaction.member_id == Member.id)
        .where(Member.id == member_id)
        .order_by(page_transaction.id.desc())
    ).all()
    if not rows:
        raise NotFoundError("عضو یافت نشد")

    # Balance and page rows come from one SQL statement/snapshot; a concurrent
    # write cannot make the displayed balance disagree with its returned ledger.
    balance_rial = int(rows[0].balance_rial or 0)
    entries = [row[2] for row in rows if row[2] is not None]
    has_more = len(entries) > limit
    transactions = entries[:limit]
    return {
        "member_id": member_id,
        "balance_rial": balance_rial,
        "transactions": transactions,
        "next_before_id": transactions[-1].id if has_more and transactions else None,
    }


def wallet_pay(
    db: Session, member_id: int, amount_rial: int, description: str = "", user=None
) -> Payment:
    """پرداخت از کیف‌پول — اتمیک: بررسی موجودی + بدهکاری + پرداخت paid در یک تراکنش."""
    from app.security.ownership import ensure_member_scope

    ensure_member_scope(db, user, member_id)
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

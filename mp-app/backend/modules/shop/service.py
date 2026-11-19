"""سرویس فروشگاه — کاتالوگ، سبد، سفارش، درگاه‌ها، دفتر قیمت، درخواست تأیید.

قواعد آهنین (هر کدام یک باگ واقعی را می‌بندد):

1. **قیمت هرگز از کلاینت پذیرفته نمی‌شود.** سبد فقط `product_id/variant_id/qty`
   دارد؛ مبلغ با قیمت DB محاسبه می‌شود. (دام: `checkout` با total_rial ورودی.)
2. **قیمت در لحظهٔ ثبت در `OrderItem.unit_price_rial` قفل می‌شود.**
3. **نوشتن کاتالوگ/قیمت/درگاه = super_admin.** ادمین می‌تواند `ChangeRequest`
   بسازد؛ تا تأیید مالک، هیچ رکوردی تغییر نمی‌کند.
4. **خواندن درگاه/شمارهٔ کارت برای همه مجاز است، `secret_key` هرگز.**
5. **اعتبار سبد/سفارش با مالکیت عضو کنترل می‌شود** (`ensure_member_scope`).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError, ConflictError, NotFoundError
from app.security.hierarchy import ensure_owner, rank_of
from db.models import (
    CartItem,
    ChangeRequest,
    Member,
    Order,
    OrderItem,
    PaymentGatewayConfig,
    PriceBook,
    Product,
    ProductCategory,
    ProductVariant,
    User,
)

MAX_QTY_PER_ITEM = 20
ONLINE_PURCHASE_CLOSED = "shop_online_closed"


# ── وضعیت فروشگاه (فاز ۲) ──


def _shop_settings():
    """تنظیم‌ها هر بار خوانده می‌شوند تا تست بتواند monkeypatch کند."""
    from app.config import settings

    return settings


def store_status(*, now: datetime | None = None) -> dict:
    """وضعیت فروشگاه از دید سرور — منبع حقیقت برای کلاینت.

    سه علت ممکن است: باز، خارج از ساعت کاری، تعطیلی هفتگی. وقتی خرید
    درون‌برنامه‌ای خاموش است، `online_purchase` همیشه False است و کلاینت
    نباید دکمهٔ خرید را نشان دهد — حتی اگر ساعت کاری باز باشد.
    """
    settings = _shop_settings()
    zone = ZoneInfo(settings.shop_timezone)
    moment = (now or datetime.now(UTC)).astimezone(zone)
    opens_at = time(hour=settings.shop_open_hour)
    closes_at = time(hour=settings.shop_close_hour)
    closed_days = {
        int(chunk.strip())
        for chunk in settings.shop_closed_weekdays.split(",")
        if chunk.strip()
    }
    if moment.weekday() in closed_days:
        reason = "weekly_holiday"
    elif opens_at <= moment.time() < closes_at and settings.shop_open_hour != settings.shop_close_hour:
        reason = "open"
    else:
        reason = "outside_hours"
    return {
        "mode": "in_person",
        "is_open": reason == "open",
        "reason": reason,
        "opens_at": f"{opens_at.hour:02d}:{opens_at.minute:02d}",
        "closes_at": f"{closes_at.hour:02d}:{closes_at.minute:02d}",
        "timezone": settings.shop_timezone,
        "closed_weekdays": sorted(closed_days),
        "online_purchase": bool(settings.shop_online_purchase_enabled),
        "checked_at": moment.isoformat(),
    }


def assert_online_purchase_open() -> None:
    """fail-closed: خرید درون‌برنامه‌ای بسته است، مگر صریح روشن شود.

    چرا این تابع و نه شرط در هر endpoint: سه مسیر نوشتن سبد و تسویه دارند؛
    اگر شرط تکرار شود، یک مسیر جا می‌ماند و همان یکی دروازهٔ دور زدن می‌شود.
    """
    if not _shop_settings().shop_online_purchase_enabled:
        raise ConflictError(
            "خرید درون‌برنامه‌ای بسته است؛ خرید حضوری در ساعات کاری باشگاه انجام می‌شود",
            code=ONLINE_PURCHASE_CLOSED,
        )
STATUS_FLOW = {"pending", "paid", "failed", "cancelled", "delivered"}


# ── کاتالوگ (خواندن: همهٔ نقش‌های وارد‌شده) ──


def list_categories(db: Session, *, include_inactive: bool = False) -> list[dict]:
    stmt = select(ProductCategory).order_by(ProductCategory.sort_order, ProductCategory.id)
    if not include_inactive:
        stmt = stmt.where(ProductCategory.is_active.is_(True))
    return [
        {
            "id": c.id,
            "slug": c.slug,
            "title": c.title,
            "kind": c.kind,
            "sort_order": c.sort_order,
            "is_active": bool(c.is_active),
        }
        for c in db.scalars(stmt)
    ]


def _variant_price(product: Product, variant: ProductVariant | None) -> int:
    if variant is not None and variant.price_rial:
        return int(variant.price_rial)
    return int(product.price_rial)


def list_products(
    db: Session,
    *,
    category: str | None = None,
    kind: str | None = None,
    search: str | None = None,
    limit: int = 100,
    include_inactive: bool = False,
) -> list[dict]:
    stmt = select(Product).order_by(Product.id.desc()).limit(limit)
    if not include_inactive:
        stmt = stmt.where(Product.is_active.is_(True))
    if category:
        cat = db.scalar(select(ProductCategory).where(ProductCategory.slug == category))
        if cat is None:
            return []
        stmt = stmt.where(Product.category_id == cat.id)
    if kind:
        cat_ids = [
            c.id for c in db.scalars(select(ProductCategory).where(ProductCategory.kind == kind))
        ]
        stmt = stmt.where(Product.category_id.in_(cat_ids or [-1]))
    if search:
        stmt = stmt.where(Product.title.ilike(f"%{search}%"))

    products = list(db.scalars(stmt))
    variants: dict[int, list[ProductVariant]] = {}
    if products:
        for v in db.scalars(
            select(ProductVariant)
            .where(ProductVariant.product_id.in_([p.id for p in products]))
            .order_by(ProductVariant.id)
        ):
            variants.setdefault(v.product_id, []).append(v)
    return [_product_dict(p, variants.get(p.id, [])) for p in products]


def _product_dict(p: Product, variants: list[ProductVariant] | None = None) -> dict:
    return {
        "id": p.id,
        "sku": p.sku,
        "title": p.title,
        "subtitle": p.subtitle,
        "description": p.description,
        "price_rial": p.price_rial,
        "compare_at_rial": p.compare_at_rial,
        "image_url": p.image_url,
        "gallery": json.loads(p.gallery_json or "[]"),
        "category_id": p.category_id,
        "stock_qty": p.stock_qty,
        "is_active": bool(p.is_active),
        "variants": [
            {
                "id": v.id,
                "label": v.label,
                "price_rial": v.price_rial if v.price_rial is not None else p.price_rial,
                "stock_qty": v.stock_qty,
                "is_active": bool(v.is_active),
            }
            for v in (variants or [])
        ],
    }


def get_product(db: Session, product_id: int) -> dict:
    p = db.get(Product, product_id)
    if p is None:
        raise NotFoundError("محصول یافت نشد")
    variants = list(db.scalars(select(ProductVariant).where(ProductVariant.product_id == p.id)))
    return _product_dict(p, variants)


# ── نوشتن کاتالوگ (فقط super_admin) ──


def create_product(db: Session, *, actor: User, payload: dict, branch_id: int = 1) -> Product:
    ensure_owner(actor.role, "ساخت محصول")
    category_id = payload.get("category_id")
    if category_id is None and payload.get("category_slug"):
        cat = db.scalar(
            select(ProductCategory).where(ProductCategory.slug == payload["category_slug"])
        )
        if cat is None:
            raise NotFoundError("دسته یافت نشد")
        category_id = cat.id
    if category_id is None or db.get(ProductCategory, int(category_id)) is None:
        raise NotFoundError("دستهٔ محصول یافت نشد")
    sku = (payload.get("sku") or "").strip()
    if not sku:
        raise ApiError("SKU اجباری است", code="sku_required")
    if db.scalar(select(Product).where(Product.sku == sku)) is not None:
        raise ConflictError("SKU تکراری است")
    price = int(payload.get("price_rial") or 0)
    if price < 0:
        raise ApiError("قیمت نمی‌تواند منفی باشد", code="bad_price")

    product = Product(
        category_id=int(category_id),
        sku=sku,
        title=payload["title"],
        subtitle=payload.get("subtitle", ""),
        description=payload.get("description", ""),
        price_rial=price,
        compare_at_rial=payload.get("compare_at_rial"),
        image_url=payload.get("image_url", ""),
        gallery_json=json.dumps(payload.get("gallery", []), ensure_ascii=False),
        stock_qty=int(payload.get("stock_qty") or 0),
        is_active=bool(payload.get("is_active", True)),
        created_by=actor.id,
        branch_id=branch_id,
    )
    db.add(product)
    db.flush()
    for v in payload.get("variants") or []:
        db.add(
            ProductVariant(
                product_id=product.id,
                label=v["label"],
                price_rial=v.get("price_rial"),
                stock_qty=int(v.get("stock_qty") or 0),
            )
        )
    db.commit()
    db.refresh(product)
    _audit(db, actor.id, "product_create", "product", product.id, {"sku": sku})
    return product


def update_product(db: Session, *, actor: User, product_id: int, payload: dict) -> Product:
    ensure_owner(actor.role, "ویرایش محصول/قیمت")
    product = db.get(Product, product_id)
    if product is None:
        raise NotFoundError("محصول یافت نشد")
    before = {"price_rial": product.price_rial, "is_active": bool(product.is_active)}
    if "price_rial" in payload and payload["price_rial"] is not None:
        price = int(payload["price_rial"])
        if price < 0:
            raise ApiError("قیمت نمی‌تواند منفی باشد", code="bad_price")
        product.price_rial = price
    for field in ("title", "subtitle", "description", "image_url", "compare_at_rial"):
        if payload.get(field) is not None:
            setattr(product, field, payload[field])
    if payload.get("stock_qty") is not None:
        product.stock_qty = int(payload["stock_qty"])
    if payload.get("is_active") is not None:
        product.is_active = bool(payload["is_active"])
    db.commit()
    db.refresh(product)
    _audit(
        db,
        actor.id,
        "product_update",
        "product",
        product.id,
        {"before": before, "after": {"price_rial": product.price_rial}},
    )
    return product


# ── سبد خرید ──


def _own_member(db: Session, user: User) -> Member:
    m = db.scalar(select(Member).where(Member.user_id == user.id))
    if m is None:
        raise NotFoundError("پروندهٔ عضو یافت نشد — ابتدا پروفایل را کامل کنید")
    return m


def add_to_cart(
    db: Session, *, user: User, product_id: int, qty: int = 1, variant_id: int | None = None
) -> dict:
    member = _own_member(db, user)
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise NotFoundError("محصول یافت نشد یا غیرفعال است")
    if qty < 1 or qty > MAX_QTY_PER_ITEM:
        raise ApiError(f"تعداد باید بین ۱ و {MAX_QTY_PER_ITEM} باشد", code="bad_qty")
    variant = None
    if variant_id is not None:
        variant = db.get(ProductVariant, variant_id)
        if variant is None or variant.product_id != product.id or not variant.is_active:
            raise NotFoundError("تنوع محصول یافت نشد")
    stock = variant.stock_qty if variant is not None else product.stock_qty
    raw = db.scalar(
        select(CartItem).where(
            CartItem.member_id == member.id,
            CartItem.product_id == product.id,
            CartItem.variant_id == variant_id if variant_id else CartItem.variant_id.is_(None),
        )
    )
    total = (raw.qty if raw else 0) + qty
    if stock >= 0 and total > stock:
        raise ConflictError(f"موجودی کافی نیست (موجود: {stock})")
    if raw:
        raw.qty = total
    else:
        db.add(
            CartItem(
                member_id=member.id,
                product_id=product.id,
                variant_id=variant_id,
                qty=qty,
            )
        )
    db.commit()
    return get_cart(db, user=user)


def get_cart(db: Session, *, user: User) -> dict:
    member = _own_member(db, user)
    items = list(db.scalars(select(CartItem).where(CartItem.member_id == member.id)))
    lines: list[dict] = []
    total = 0
    for item in items:
        product = db.get(Product, item.product_id)
        if product is None:
            continue
        variant = db.get(ProductVariant, item.variant_id) if item.variant_id else None
        unit = _variant_price(product, variant)
        total += unit * item.qty
        lines.append(
            {
                "id": item.id,
                "product_id": product.id,
                "variant_id": item.variant_id,
                "title": product.title,
                "variant_label": variant.label if variant else "",
                "image_url": product.image_url,
                "unit_price_rial": unit,
                "qty": item.qty,
                "line_total_rial": unit * item.qty,
            }
        )
    return {"member_id": member.id, "items": lines, "total_rial": total, "count": len(lines)}


def update_cart_item(db: Session, *, user: User, item_id: int, qty: int) -> dict:
    member = _own_member(db, user)
    item = db.get(CartItem, item_id)
    if item is None or item.member_id != member.id:
        raise NotFoundError("قلم سبد یافت نشد")
    if qty <= 0:
        db.delete(item)
    else:
        if qty > MAX_QTY_PER_ITEM:
            raise ApiError(f"حداکثر {MAX_QTY_PER_ITEM} عدد", code="bad_qty")
        item.qty = qty
    db.commit()
    return get_cart(db, user=user)


def remove_cart_item(db: Session, *, user: User, item_id: int) -> dict:
    return update_cart_item(db, user=user, item_id=item_id, qty=0)


# ── تسویه ──


def checkout(db: Session, *, user: User, method: str = "wallet", note: str = "") -> Order:
    """سبد ← سفارش. مبلغ از DB، نه از کلاینت. پرداخت از کیف‌پول یا درگاه."""
    from app.security.ownership import ensure_member_scope
    from modules.payments import service as payments

    cart = get_cart(db, user=user)
    if not cart["items"]:
        raise ApiError("سبد خرید خالی است", code="empty_cart")
    member_id = cart["member_id"]
    ensure_member_scope(db, user, member_id)

    order = Order(
        member_id=member_id,
        status="pending",
        total_rial=cart["total_rial"],
        note=note,
        branch_id=1,
    )
    db.add(order)
    db.flush()
    for line in cart["items"]:
        product = db.get(Product, line["product_id"])
        variant = db.get(ProductVariant, line["variant_id"]) if line["variant_id"] else None
        stock = variant.stock_qty if variant is not None else (product.stock_qty if product else 0)
        if stock >= 0 and stock < line["qty"]:
            raise ConflictError(f"موجودی «{line['title']}» کافی نیست")
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=line["product_id"],
                variant_id=line["variant_id"],
                title_snapshot=line["title"],
                unit_price_rial=line["unit_price_rial"],
                qty=line["qty"],
            )
        )
        if variant is not None and variant.stock_qty >= 0:
            variant.stock_qty -= line["qty"]
        elif product is not None and product.stock_qty >= 0:
            product.stock_qty -= line["qty"]

    payment = payments.create_payment(
        db,
        member_id,
        order.total_rial,
        method=method,
        description=f"سفارش #{order.id}",
        user=user,
    )
    order.payment_id = payment.id

    if method == "wallet":
        # پرداخت از کیف‌پول: برداشت + تسویه در یک تراکنش.
        paid = payments.wallet_pay(db, member_id, order.total_rial, f"سفارش #{order.id}", user=user)
        order.status = "paid"
        order.payment_id = paid.id
    else:
        order.status = "pending"

    # سبد خالی می‌شود فقط وقتی سفارش ثبت شد (اگر خطا داد، سبد می‌ماند).
    for item in db.scalars(select(CartItem).where(CartItem.member_id == member_id)):
        db.delete(item)
    db.commit()
    db.refresh(order)
    _audit(
        db,
        user.id,
        "order_checkout",
        "order",
        order.id,
        {"total_rial": order.total_rial, "method": method},
    )
    return order


def list_orders(db: Session, *, user: User, limit: int = 50) -> list[dict]:
    from app.security.ownership import get_own_member

    stmt = select(Order).order_by(Order.id.desc()).limit(limit)
    if user.role == "member":
        own = get_own_member(db, user)
        stmt = stmt.where(Order.member_id == (own.id if own else -1))
    orders = list(db.scalars(stmt))
    out = []
    for o in orders:
        items = list(db.scalars(select(OrderItem).where(OrderItem.order_id == o.id)))
        out.append(
            {
                "id": o.id,
                "member_id": o.member_id,
                "status": o.status,
                "total_rial": o.total_rial,
                "payment_id": o.payment_id,
                "note": o.note,
                "created_at": o.created_at,
                "items": [
                    {
                        "product_id": i.product_id,
                        "title": i.title_snapshot,
                        "unit_price_rial": i.unit_price_rial,
                        "qty": i.qty,
                    }
                    for i in items
                ],
            }
        )
    return out


def mark_order(db: Session, *, user: User, order_id: int, status: str) -> dict:
    """جابه‌جایی وضعیت سفارش توسط کادر — گذار نامعتبر رد می‌شود."""
    if rank_of(user.role) < rank_of("reception"):
        raise ApiError("فقط کادر می‌تواند وضعیت سفارش را تغییر دهد", code="forbidden")
    if status not in STATUS_FLOW:
        raise ApiError("وضعیت نامعتبر", code="bad_status")
    order = db.get(Order, order_id)
    if order is None:
        raise NotFoundError("سفارش یافت نشد")
    allowed = {
        "pending": {"paid", "failed", "cancelled"},
        "paid": {"delivered", "cancelled"},
        "failed": {"pending"},
        "cancelled": set(),
        "delivered": set(),
    }
    if status not in allowed[order.status]:
        raise ConflictError(f"گذار {order.status} → {status} مجاز نیست")
    order.status = status
    db.commit()
    db.refresh(order)
    _audit(db, user.id, "order_status", "order", order.id, {"status": status})
    return {"id": order.id, "status": order.status}


# ── درگاه‌ها و شمارهٔ کارت ──


def _mask_card(number: str) -> str:
    digits = "".join(ch for ch in number if ch.isdigit())
    if len(digits) < 8:
        return number
    return f"{digits[:4]}-****-****-{digits[-4:]}"


def list_gateways(db: Session, *, include_secret: bool = False) -> list[dict]:
    rows = list(db.scalars(select(PaymentGatewayConfig).order_by(PaymentGatewayConfig.id)))
    out = []
    for g in rows:
        row = {
            "id": g.id,
            "kind": g.kind,
            "title": g.title,
            "is_enabled": bool(g.is_enabled),
            "card_number_masked": _mask_card(g.card_number) if g.card_number else "",
            "card_holder": g.card_holder,
            "bank_name": g.bank_name,
            "public_key": g.public_key,
            "instructions": g.instructions,
            # کلید خصوصی هرگز برنمی‌گردد — فقط «تنظیم شده یا نه».
            "secret_configured": bool(g.secret_key),
        }
        if include_secret:  # هیچ مسیری این را true صدا نمی‌زند؛ برای تست‌پذیری
            row["secret_key"] = g.secret_key
        out.append(row)
    return out


def upsert_gateway(
    db: Session, *, actor: User, payload: dict, gateway_id: int | None = None
) -> dict:
    ensure_owner(actor.role, "افزودن/ویرایش درگاه و شمارهٔ کارت")
    kind = payload["kind"]
    config: PaymentGatewayConfig | None
    if gateway_id is not None:
        config = db.get(PaymentGatewayConfig, gateway_id)
        if config is None:
            raise NotFoundError("درگاه یافت نشد")
    else:
        config = db.scalar(select(PaymentGatewayConfig).where(PaymentGatewayConfig.kind == kind))
    before = None if config is None else {"kind": config.kind, "is_enabled": config.is_enabled}
    if config is None:
        config = PaymentGatewayConfig(kind=kind, title=payload["title"])
        db.add(config)
    config.title = payload["title"]
    config.is_enabled = bool(payload.get("is_enabled", False))
    if payload.get("card_number"):
        digits = "".join(ch for ch in payload["card_number"] if ch.isdigit())
        if len(digits) != 16:
            raise ApiError("شمارهٔ کارت باید ۱۶ رقم باشد", code="bad_card")
        config.card_number = digits
    if payload.get("card_holder") is not None:
        config.card_holder = payload["card_holder"]
    if payload.get("bank_name") is not None:
        config.bank_name = payload["bank_name"]
    if payload.get("public_key") is not None:
        config.public_key = payload["public_key"]
    if payload.get("secret_key"):
        config.secret_key = payload["secret_key"]
    if payload.get("instructions") is not None:
        config.instructions = payload["instructions"]
    config.updated_by = actor.id
    db.commit()
    db.refresh(config)
    _audit(
        db,
        actor.id,
        "gateway_upsert",
        "gateway",
        config.id,
        {"before": before, "kind": config.kind},
    )
    return (
        list_gateways(db)[-1]
        if gateway_id is None
        else next(g for g in list_gateways(db) if g["id"] == config.id)
    )


# ── دفتر قیمت خدمات (اشتراک/مربی/برنامه) ──


def list_prices(db: Session, *, category: str | None = None) -> list[dict]:
    stmt = select(PriceBook).where(PriceBook.is_active.is_(True)).order_by(PriceBook.id)
    if category:
        stmt = stmt.where(PriceBook.category == category)
    return [
        {
            "id": p.id,
            "category": p.category,
            "code": p.code,
            "title": p.title,
            "price_rial": p.price_rial,
            "duration_days": p.duration_days,
            "gender": p.gender,
            "effective_from": p.effective_from,
        }
        for p in db.scalars(stmt)
    ]


def upsert_price(db: Session, *, actor: User, payload: dict, price_id: int | None = None) -> dict:
    ensure_owner(actor.role, "قیمت‌گذاری خدمات")
    row = (
        db.get(PriceBook, price_id)
        if price_id is not None
        else db.scalar(
            select(PriceBook).where(
                PriceBook.category == payload["category"], PriceBook.code == payload["code"]
            )
        )
    )
    if row is None:
        row = PriceBook(
            category=payload["category"],
            code=payload["code"],
            title=payload["title"],
            price_rial=int(payload["price_rial"]),
        )
        db.add(row)
    row.title = payload.get("title", row.title)
    row.price_rial = int(payload.get("price_rial", row.price_rial))
    row.duration_days = payload.get("duration_days", row.duration_days)
    row.gender = payload.get("gender", row.gender)
    row.is_active = bool(payload.get("is_active", True))
    row.updated_by = actor.id
    db.commit()
    db.refresh(row)
    _audit(db, actor.id, "price_upsert", "price_book", row.id, {"price_rial": row.price_rial})
    return {
        "id": row.id,
        "category": row.category,
        "code": row.code,
        "title": row.title,
        "price_rial": row.price_rial,
        "duration_days": row.duration_days,
        "gender": row.gender,
    }


# ── درخواست تغییر (ادمین ← تأیید مالک) ──

REQUEST_KINDS = {
    "product_create": "ساخت محصول",
    "product_price": "تغییر قیمت محصول",
    "gateway_upsert": "افزودن/ویرایش درگاه",
    "membership_price": "قیمت اشتراک",
    "coach_fee": "شهریهٔ مربی",
    "program_fee": "هزینهٔ برنامه",
}


def create_change_request(db: Session, *, actor: User, kind: str, payload: dict) -> dict:
    """ادمین پیشنهاد می‌دهد. تا تأیید مالک، **هیچ رکوردی** تغییر نمی‌کند."""
    if kind not in REQUEST_KINDS:
        raise ApiError("نوع درخواست نامعتبر", code="bad_kind")
    if rank_of(actor.role) < rank_of("admin"):
        raise ApiError("فقط admin یا بالاتر می‌تواند درخواست تغییر ثبت کند", code="forbidden")
    req = ChangeRequest(
        kind=kind,
        payload_json=json.dumps(payload, ensure_ascii=False),
        requested_by=actor.id,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    _audit(db, actor.id, "change_request_create", "change_request", req.id, {"kind": kind})
    return _request_dict(req)


def _request_dict(r: ChangeRequest) -> dict:
    return {
        "id": r.id,
        "kind": r.kind,
        "kind_label": REQUEST_KINDS.get(r.kind, r.kind),
        "payload": json.loads(r.payload_json or "{}"),
        "requested_by": r.requested_by,
        "status": r.status,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at,
        "review_note": r.review_note,
        "result": json.loads(r.result_json or "{}"),
        "created_at": r.created_at,
    }


def list_change_requests(db: Session, *, user: User, status: str | None = None) -> list[dict]:
    stmt = select(ChangeRequest).order_by(ChangeRequest.id.desc()).limit(200)
    # ادمین فقط درخواست‌های خودش را می‌بیند؛ مالک همه را.
    if rank_of(user.role) < rank_of("super_admin"):
        stmt = stmt.where(ChangeRequest.requested_by == user.id)
    if status:
        stmt = stmt.where(ChangeRequest.status == status)
    return [_request_dict(r) for r in db.scalars(stmt)]


def review_change_request(
    db: Session, *, actor: User, request_id: int, approve: bool, note: str = ""
) -> dict:
    ensure_owner(actor.role, "تأیید/رد درخواست تغییر")
    req = db.get(ChangeRequest, request_id)
    if req is None:
        raise NotFoundError("درخواست یافت نشد")
    if req.status != "pending":
        raise ConflictError("این درخواست قبلاً بررسی شده است")
    if req.requested_by == actor.id:
        raise ApiError("تأیید درخواست خودتان مجاز نیست", code="self_review")

    result: dict = {}
    if approve:
        payload = json.loads(req.payload_json or "{}")
        # اعمال با اختیار **مالک** انجام می‌شود، نه ادمین درخواست‌دهنده:
        # تأیید مالک همان مجوزی است که سرویس‌های اقتصادی می‌خواهند. اگر
        # actor همان ادمین می‌ماند، `ensure_owner` رد می‌کرد و «تأیید»
        # هیچ اثری نداشت (باگ که تست همین‌جا گرفت).
        try:
            result = _apply(db, req.kind, payload, actor=actor)
        except ApiError:
            db.rollback()
            raise
        result["requested_by"] = req.requested_by
    req.status = "approved" if approve else "rejected"
    req.reviewed_by = actor.id
    req.reviewed_at = datetime.now(UTC)
    req.review_note = note
    req.result_json = json.dumps(result, ensure_ascii=False, default=str)
    db.commit()
    db.refresh(req)
    _audit(
        db,
        actor.id,
        "change_request_review",
        "change_request",
        req.id,
        {"approved": approve, "kind": req.kind},
    )
    return _request_dict(req)


def _apply(db: Session, kind: str, payload: dict, *, actor: User) -> dict:
    """اعمال تأییدشده — با همان سرویس‌هایی که مسیر مستقیم مالک استفاده می‌کند."""
    if kind == "product_create":
        p = create_product(db, actor=actor, payload=payload)
        return {"product_id": p.id}
    if kind == "product_price":
        p = update_product(db, actor=actor, product_id=int(payload["product_id"]), payload=payload)
        return {"product_id": p.id, "price_rial": p.price_rial}
    if kind == "gateway_upsert":
        return {"gateway": upsert_gateway(db, actor=actor, payload=payload)}
    if kind in ("membership_price", "coach_fee", "program_fee"):
        mapped = {
            "membership_price": "membership",
            "coach_fee": "coach_fee",
            "program_fee": "program_fee",
        }[kind]
        row = upsert_price(db, actor=actor, payload={**payload, "category": mapped})
        return {"price": row}
    raise ApiError("نوع درخواست پشتیبانی نمی‌شود", code="bad_kind")


def _audit(
    db: Session, actor_id: int | None, action: str, entity: str, entity_id: int, detail: dict
) -> None:
    from modules.admin.service import audit

    audit(db, actor_id, action, entity, entity_id, detail)

"""روتر فروشگاه — کاتالوگ، سبد، سفارش، درگاه، دفتر قیمت، درخواست تأیید.

نگاشت به خواستهٔ کاربر (۱۴۰۵-۰۸-۲۴):
- «فروشگاه تجهیزات/مکمل»                     → `/shop/products`, `/shop/categories`
- «قیمت و محصول با عکس فقط super_admin»     → POST/PATCH با `ensure_owner`
- «ادمین بخواهد ← تأیید مالک»               → `/shop/change-requests`
- «محصول/قیمت فقط برای کاربر عادی، سبد و تسویه» → `/shop/cart`, `/shop/checkout`
- «درگاه و شمارهٔ کارت فقط super_admin»      → `/shop/gateways` (GET برای همه، نوشتن فقط مالک)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.deps import CurrentUser, DbSession, require_permission
from app.ids import Id, OptId

# همان نمونهٔ سقف نرخ که auth و main استفاده می‌کنند (slowapi). نمونهٔ دوم
# ساختن باعث می‌شود شمارنده‌ها از هم جدا شوند و سقف دور زده شود.
from modules.auth.router import limiter
from modules.shop import service

router = APIRouter(prefix="/shop", tags=["shop"], dependencies=[Depends(require_permission())])


# ── schemas ──
class VariantIn(BaseModel):
    label: str = Field(..., min_length=1, max_length=60)
    price_rial: int | None = Field(None, ge=0)
    stock_qty: int = 0


class ProductCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    sku: str = Field(..., min_length=2, max_length=40)
    category_id: OptId = None
    category_slug: str | None = None
    subtitle: str = Field("", max_length=160)
    description: str = ""
    price_rial: int = Field(..., ge=0)
    compare_at_rial: int | None = Field(None, ge=0)
    image_url: str = Field("", max_length=300)
    gallery: list[str] = Field(default_factory=list)
    stock_qty: int = 0
    is_active: bool = True
    variants: list[VariantIn] = Field(default_factory=list)


class ProductUpdate(BaseModel):
    title: str | None = None
    subtitle: str | None = None
    description: str | None = None
    price_rial: int | None = Field(None, ge=0)
    compare_at_rial: int | None = None
    image_url: str | None = None
    stock_qty: int | None = None
    is_active: bool | None = None


class CartAdd(BaseModel):
    # M60/R18 — بدون سقف، `product_id: 10**30` به SQLite می‌رسید و ۵۰۰ می‌داد.
    product_id: Id
    variant_id: OptId = None
    qty: int = Field(1, ge=1, le=20)


class CartUpdate(BaseModel):
    qty: int = Field(..., ge=0, le=20)


class CheckoutIn(BaseModel):
    method: str = Field("wallet", pattern="^(wallet|card|cash|card_to_card)$")
    note: str = Field("", max_length=200)


class GatewayIn(BaseModel):
    # درگاه اینترنتی حذف شده؛ فقط کارت‌به‌کارت و نقدی.
    kind: str = Field(..., pattern="^(card_to_card|cash)$")
    title: str = Field(..., min_length=2, max_length=80)
    is_enabled: bool = False
    card_number: str = Field("", max_length=30)
    card_holder: str = Field("", max_length=80)
    bank_name: str = Field("", max_length=60)
    public_key: str = Field("", max_length=120)
    secret_key: str = Field("", max_length=200)
    instructions: str = ""


class PriceIn(BaseModel):
    category: str = Field(..., pattern="^(membership|coach_fee|program_fee)$")
    code: str = Field(..., min_length=2, max_length=40)
    title: str = Field(..., min_length=2, max_length=120)
    price_rial: int = Field(..., ge=0)
    duration_days: int | None = Field(None, ge=1, le=730)
    gender: str = Field("any", pattern="^(any|male|female)$")
    is_active: bool = True


class ChangeRequestIn(BaseModel):
    kind: str = Field(
        ...,
        pattern="^(product_create|product_price|gateway_upsert|membership_price|coach_fee|program_fee)$",
    )
    payload: dict = Field(default_factory=dict)


class ReviewIn(BaseModel):
    approve: bool
    note: str = Field("", max_length=200)


class OrderStatusIn(BaseModel):
    status: str = Field(..., pattern="^(pending|paid|failed|cancelled|delivered)$")


# ── کاتالوگ ──
@router.get("/status", summary="وضعیت فروشگاه (باز/بسته + علت + حالت خرید)")
def status(user: CurrentUser):
    """منبع حقیقت باز/بسته بودن؛ کلاینت نباید ساعت دستگاه را جای آن بگذارد."""
    return service.store_status()


@router.get("/categories", summary="دسته‌های فروشگاه")
def categories(db: DbSession, user: CurrentUser, include_inactive: bool = False):
    from app.security.hierarchy import rank_of

    return service.list_categories(
        db, include_inactive=include_inactive and rank_of(user.role) >= rank_of("super_admin")
    )


@router.get("/products", summary="فهرست محصولات (فروشگاه)")
def products(
    db: DbSession,
    user: CurrentUser,
    category: str | None = Query(None),
    kind: str | None = Query(None, pattern="^(equipment|supplement|apparel|service)$"),
    search: str | None = Query(None, max_length=60),
    limit: int = Query(100, ge=1, le=200),
):
    return service.list_products(db, category=category, kind=kind, search=search, limit=limit)


@router.get("/products/{product_id}", summary="جزئیات محصول")
def product_detail(product_id: int, db: DbSession, user: CurrentUser):
    return service.get_product(db, product_id)


@router.post("/products", summary="ساخت محصول (فقط super_admin)")
def create_product(payload: ProductCreate, db: DbSession, user: CurrentUser):
    p = service.create_product(db, actor=user, payload=payload.model_dump())
    return service.get_product(db, p.id)


@router.patch("/products/{product_id}", summary="ویرایش محصول/قیمت (فقط super_admin)")
def update_product(product_id: int, payload: ProductUpdate, db: DbSession, user: CurrentUser):
    service.update_product(
        db, actor=user, product_id=product_id, payload=payload.model_dump(exclude_unset=True)
    )
    return service.get_product(db, product_id)


# ── سبد و تسویه ──
@router.get("/cart", summary="سبد خرید من")
def cart(db: DbSession, user: CurrentUser):
    return service.get_cart(db, user=user)


@router.post("/cart", summary="افزودن به سبد (بسته در فروشگاه نمایش‌محور)")
@limiter.limit(settings.shop_write_rate_limit)
def cart_add(request: Request, payload: CartAdd, db: DbSession, user: CurrentUser):
    # فاز ۲ — fail-closed قبل از هر نوشتن: اول بسته بودن، بعد بقیهٔ قواعد.
    service.assert_online_purchase_open()
    # M60 — چرا سقف: بدون آن، حلقهٔ سبد/تسویه همهٔ موجودی را رزرو می‌کند
    # (نوعی DoS روی موجودی). `request` اول است چون slowapi امضای آن را
    # از decorated function می‌خواند.
    return service.add_to_cart(
        db,
        user=user,
        product_id=payload.product_id,
        qty=payload.qty,
        variant_id=payload.variant_id,
    )


@router.patch("/cart/{item_id}", summary="تغییر تعداد قلم سبد (بسته)")
@limiter.limit(settings.shop_write_rate_limit)
def cart_update(
    request: Request, item_id: int, payload: CartUpdate, db: DbSession, user: CurrentUser
):
    service.assert_online_purchase_open()
    return service.update_cart_item(db, user=user, item_id=item_id, qty=payload.qty)


@router.delete("/cart/{item_id}", summary="حذف قلم سبد (بسته)")
@limiter.limit(settings.shop_write_rate_limit)
def cart_remove(request: Request, item_id: int, db: DbSession, user: CurrentUser):
    service.assert_online_purchase_open()
    return service.remove_cart_item(db, user=user, item_id=item_id)


@router.post("/checkout", summary="تسویهٔ سبد ← سفارش (بسته: خرید حضوری است)")
@limiter.limit(settings.shop_checkout_rate_limit)
def checkout(request: Request, payload: CheckoutIn, db: DbSession, user: CurrentUser):
    service.assert_online_purchase_open()
    # M60 — سقف سخت‌گیرانه‌تر: هر تسویه یک تراکنش پول است.
    order = service.checkout(db, user=user, method=payload.method, note=payload.note)
    return {
        "order_id": order.id,
        "status": order.status,
        "total_rial": order.total_rial,
        "payment_id": order.payment_id,
    }


@router.get("/orders", summary="سفارش‌های من (کادر: همه)")
def orders(db: DbSession, user: CurrentUser, limit: int = Query(50, ge=1, le=200)):
    return service.list_orders(db, user=user, limit=limit)


@router.get("/orders/{order_id}/receipt", summary="رسید سفارش (چاپ/تحویل — R5)")
def order_receipt(order_id: int, db: DbSession, user: CurrentUser):
    """رسید قابل‌چاپ سفارش: اقلام، جمع، و پرداخت مرتبط.

    کنترل مالکیت داخل سرویس است (عضو فقط سفارش خودش) — مسیر عمداً از
    `ensure_owner` نمی‌گذرد چون عضو باید رسید سفارش خودش را ببیند.
    """
    from modules.payments.invoice import build_order_receipt

    return build_order_receipt(db, order_id, user=user)


@router.patch("/orders/{order_id}", summary="تغییر وضعیت سفارش (کادر)")
def order_status(order_id: int, payload: OrderStatusIn, db: DbSession, user: CurrentUser):
    return service.mark_order(db, user=user, order_id=order_id, status=payload.status)


# ── درگاه‌ها ──
@router.get("/gateways", summary="درگاه‌ها و شمارهٔ کارت (خواندن برای همه — کلید خصوصی هرگز)")
def gateways(db: DbSession, user: CurrentUser):
    return service.list_gateways(db)


@router.post("/gateways", summary="افزودن/ویرایش درگاه (فقط super_admin)")
def gateway_create(payload: GatewayIn, db: DbSession, user: CurrentUser):
    return service.upsert_gateway(db, actor=user, payload=payload.model_dump())


@router.put("/gateways/{gateway_id}", summary="ویرایش درگاه (فقط super_admin)")
def gateway_update(gateway_id: int, payload: GatewayIn, db: DbSession, user: CurrentUser):
    return service.upsert_gateway(
        db, actor=user, payload=payload.model_dump(), gateway_id=gateway_id
    )


# ── دفتر قیمت ──
@router.get("/prices", summary="دفتر قیمت (اشتراک/شهریهٔ مربی/هزینهٔ برنامه)")
def prices(
    db: DbSession,
    user: CurrentUser,
    category: str | None = Query(None, pattern="^(membership|coach_fee|program_fee)$"),
):
    return service.list_prices(db, category=category)


@router.post("/prices", summary="ثبت/به‌روزرسانی قیمت (فقط super_admin)")
def price_upsert(payload: PriceIn, db: DbSession, user: CurrentUser):
    return service.upsert_price(db, actor=user, payload=payload.model_dump())


# ── درخواست تغییر (ادمین ← تأیید مالک) ──
@router.get("/change-requests", summary="درخواست‌های تغییر (ادمین: خودش، مالک: همه)")
def change_requests(
    db: DbSession,
    user: CurrentUser,
    status: str | None = Query(None, pattern="^(pending|approved|rejected)$"),
):
    return service.list_change_requests(db, user=user, status=status)


@router.post("/change-requests", summary="ثبت درخواست تغییر قیمت/محصول/درگاه (admin)")
def change_request_create(payload: ChangeRequestIn, db: DbSession, user: CurrentUser):
    return service.create_change_request(db, actor=user, kind=payload.kind, payload=payload.payload)


@router.post(
    "/change-requests/{request_id}/review",
    summary="تأیید/رد درخواست تغییر (فقط super_admin)",
)
def change_request_review(request_id: int, payload: ReviewIn, db: DbSession, user: CurrentUser):
    return service.review_change_request(
        db, actor=user, request_id=request_id, approve=payload.approve, note=payload.note
    )

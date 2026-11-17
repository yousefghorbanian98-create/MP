"""مدل‌های فروشگاه — دسته، محصول، رسانه، سبد، سفارش، و **درخواست تأیید قیمت**.

الگو از فروشگاه‌های باشگاهی (REA teardown — `docs/MuscleParadise/COMPETITIVE-*`)
گرفته شده، نه از صفر:

| الگوی رقیب | معادل ما |
|---|---|
| Catalog → Category → Variant (سایز/طعم) | `ProductCategory` → `Product` → `ProductVariant` |
| Inventory per branch | `ProductVariant.stock_qty` + `branch_id` (BranchMixin) |
| Cart → Order → OrderItem (قیمت در لحظهٔ ثبت قفل می‌شود) | `Cart`/`CartItem`، `Order`/`OrderItem.unit_price_rial` |
| «قیمت فقط از طرف مالک» (approval workflow) | `ChangeRequest` — ادمین پیشنهاد می‌دهد، مالک تأیید می‌کند |

**چرا `unit_price_rial` در `OrderItem` تکرار می‌شود؟** اگر قیمت محصول بعداً
عوض شود، فاکتور دیروز نباید عوض شود. این همان دامی است که در `members_summary`
با خواندن ستون‌ها به‌صورت positional خوردیم؛ اینجا صریح قفل می‌شود.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base, BranchMixin, TimestampMixin


class ProductCategory(TimestampMixin, Base):
    """دستهٔ فروشگاه — مکمل، پوشاک، تجهیزات."""

    __tablename__ = "product_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False, default="equipment"
    )  # equipment | supplement | apparel | service
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Product(TimestampMixin, BranchMixin, Base):
    """محصول — قیمت پایه به ریال. نمایش فقط برای نقش member در API عمومی."""

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("product_categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    sku: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    subtitle: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    price_rial: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # قیمت پیش از تخفیف — برای نمایش «٪۳۰ تخفیف» بدون محاسبهٔ سمت کلاینت.
    compare_at_rial: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_url: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    gallery_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # عددی که در UI «موجود در انبار» نشان داده می‌شود؛ منفی = نامحدود/سرویس.
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class ProductVariant(TimestampMixin, Base):
    """تنوع محصول (سایز/طعم) — قیمت خالی یعنی «قیمت محصول» معتبر است."""

    __tablename__ = "product_variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    label: Mapped[str] = mapped_column(String(60), nullable=False)  # "۵ کیلو — شکلاتی"
    price_rial: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stock_qty: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CartItem(TimestampMixin, Base):
    """سبد خرید — یک عضو، چند قلم. به سفارش تبدیل می‌شود، نه اینکه همان باشد."""

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    qty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)


class Order(TimestampMixin, BranchMixin, Base):
    """سفارش — وضعیت فقط از پرداخت/تحویل جابه‌جا می‌شود."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(
        ForeignKey("members.id", ondelete="CASCADE"), index=True, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | paid | failed | cancelled | delivered
    total_rial: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # پرداخت مرتبط (wallet/gateway) — یک سفارش، یک پرداخت.
    payment_id: Mapped[int | None] = mapped_column(
        ForeignKey("payments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    note: Mapped[str] = mapped_column(String(200), default="", nullable=False)


class OrderItem(TimestampMixin, Base):
    """قلم سفارش — قیمت و نام در لحظهٔ ثبت **قفل** می‌شوند."""

    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL"), nullable=True
    )
    title_snapshot: Mapped[str] = mapped_column(String(120), nullable=False)
    unit_price_rial: Mapped[int] = mapped_column(Integer, nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class PaymentGatewayConfig(TimestampMixin, Base):
    """درگاه/شمارهٔ کارت — **فقط super_admin** می‌نویسد؛ بقیه فقط می‌خوانند.

    اعتبارسنجی `card_number` با ماسک ذخیره می‌شود. کلید درگاه هرگز در API
    برنمی‌گردد (`is_secret` و حذف در schema)، چون همان دام «توکن در پاسخ» است.
    """

    __tablename__ = "payment_gateway_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # zarinpal | idpay | card_to_card | cash
    title: Mapped[str] = mapped_column(String(80), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # شمارهٔ کارت/شبا — ماسک‌شده ذخیره می‌شود (هرگز کامل برنمی‌گردد).
    card_number: Mapped[str] = mapped_column(String(30), default="", nullable=False)
    card_holder: Mapped[str] = mapped_column(String(80), default="", nullable=False)
    bank_name: Mapped[str] = mapped_column(String(60), default="", nullable=False)
    # شناسهٔ عمومی درگاه (merchant id) — قابل نمایش؛ کلید خصوصی نه.
    public_key: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    secret_key: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    instructions: Mapped[str] = mapped_column(Text, default="", nullable=False)
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class ChangeRequest(TimestampMixin, Base):
    """درخواست تغییر حساس از سوی ادمین — تا تأیید مالک، **هیچ اثری ندارد**.

    چرا جدول مستقل و نه «فقط اجازه ندادن»: کاربر گفت اگر ادمین بخواهد قیمت
    بگذارد، باید ابتدا تأیید مالک را بگیرد. «۴۰۳ خالص» یعنی ادمین هیچ راهی
    ندارد؛ این جدول می‌دهد: پیشنهاد ثبت می‌شود، مالک تأیید/رد می‌کند،
    تأیید ← اعمال خودکار + AuditLog.
    """

    __tablename__ = "change_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )  # product_create | product_price | gateway_upsert | membership_price | coach_fee | program_fee
    payload_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | approved | rejected
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str] = mapped_column(String(200), default="", nullable=False)
    result_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)


class PriceBook(TimestampMixin, Base):
    """دفتر قیمت خدمات — اشتراک، شهریهٔ مربی، هزینهٔ برنامه.

    چرا جدول جدا و نه ستون در `memberships`: قیمت یک **سیاست** است، نه
    ویژگی رکورد. با جدول جدا: تاریخ اعتبار (`effective_from`)، تفکیک جنسیت
    (هم‌راستا با M41)، و تغییر بدون دست‌زدن به فاکتورهای قبلی.
    """

    __tablename__ = "price_book"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # membership | coach_fee | program_fee
    code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    price_rial: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str] = mapped_column(String(10), default="any", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

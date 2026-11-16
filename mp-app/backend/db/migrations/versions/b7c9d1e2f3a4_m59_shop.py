"""m59_c1 — فروشگاه، سبد، سفارش، درگاه/کارت، دفتر قیمت، درخواست تأیید

Revision ID: b7c9d1e2f3a4
Revises: 8a1f2c3d4e5b

چرا: سه خواستهٔ کاربر (فروشگاه تجهیزات/مکمل، کیف‌پول با درگاه و کارت‌به‌کارت،
قیمت‌گذاری فقط مالک + تأیید مالک برای ادمین) هیچ جدولی نداشتند. مدل
`ShopPage` در اپ Dart چهار محصول hardcode داشت — یعنی UI بدون داده.

جدول‌ها: product_categories, products, product_variants, cart_items,
orders, order_items, payment_gateway_configs, change_requests, price_book.

نکته: `price_book.effective_from` و همهٔ `created_at/updated_at` با
`server_default=now()` می‌آیند تا داده‌های موجود در migration نشکنند.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c9d1e2f3a4"
down_revision: str | Sequence[str] | None = "8a1f2c3d4e5b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _ts() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "product_categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(40), nullable=False),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_ts(),
    )
    op.create_index("ix_product_categories_slug", "product_categories", ["slug"], unique=True)

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "category_id",
            sa.Integer(),
            sa.ForeignKey("product_categories.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("sku", sa.String(40), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("subtitle", sa.String(160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("price_rial", sa.Integer(), nullable=False),
        sa.Column("compare_at_rial", sa.Integer(), nullable=True),
        sa.Column("image_url", sa.String(300), nullable=False),
        sa.Column("gallery_json", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("stock_qty", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_ts(),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_category_id", "products", ["category_id"])
    op.create_index("ix_products_branch_id", "products", ["branch_id"])

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("label", sa.String(60), nullable=False),
        sa.Column("price_rial", sa.Integer(), nullable=True),
        sa.Column("stock_qty", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_ts(),
    )
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])

    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "member_id",
            sa.Integer(),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            sa.Integer(),
            sa.ForeignKey("products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "variant_id",
            sa.Integer(),
            sa.ForeignKey("product_variants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("qty", sa.Integer(), nullable=False),
        *_ts(),
    )
    op.create_index("ix_cart_items_member_id", "cart_items", ["member_id"])
    op.create_index("ix_cart_items_product_id", "cart_items", ["product_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "member_id",
            sa.Integer(),
            sa.ForeignKey("members.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("total_rial", sa.Integer(), nullable=False),
        sa.Column(
            "payment_id",
            sa.Integer(),
            sa.ForeignKey("payments.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("note", sa.String(200), nullable=False),
        *_ts(),
    )
    op.create_index("ix_orders_member_id", "orders", ["member_id"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_payment_id", "orders", ["payment_id"])
    op.create_index("ix_orders_branch_id", "orders", ["branch_id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column(
            "variant_id",
            sa.Integer(),
            sa.ForeignKey("product_variants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title_snapshot", sa.String(120), nullable=False),
        sa.Column("unit_price_rial", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        *_ts(),
    )
    op.create_index("ix_order_items_order_id", "order_items", ["order_id"])

    op.create_table(
        "payment_gateway_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("title", sa.String(80), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("card_number", sa.String(30), nullable=False),
        sa.Column("card_holder", sa.String(80), nullable=False),
        sa.Column("bank_name", sa.String(60), nullable=False),
        sa.Column("public_key", sa.String(120), nullable=False),
        sa.Column("secret_key", sa.String(200), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_ts(),
    )
    op.create_index("ix_payment_gateway_configs_kind", "payment_gateway_configs", ["kind"])

    op.create_table(
        "change_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("requested_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_note", sa.String(200), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=False),
        *_ts(),
    )
    op.create_index("ix_change_requests_kind", "change_requests", ["kind"])
    op.create_index("ix_change_requests_requested_by", "change_requests", ["requested_by"])
    op.create_index("ix_change_requests_status", "change_requests", ["status"])

    op.create_table(
        "price_book",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("price_rial", sa.Integer(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "effective_from",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_ts(),
    )
    op.create_index("ix_price_book_category", "price_book", ["category"])
    op.create_index("ix_price_book_code", "price_book", ["code"])

    # `TimestampMixin.created_at` دارای index=True است — بدون این خطوط،
    # `alembic check` drift نشان می‌داد (همان دامی که در m58 بسته شد).
    op.create_index("ix_product_categories_created_at", "product_categories", ["created_at"])
    op.create_index("ix_products_created_at", "products", ["created_at"])
    op.create_index("ix_product_variants_created_at", "product_variants", ["created_at"])
    op.create_index("ix_cart_items_created_at", "cart_items", ["created_at"])
    op.create_index("ix_orders_created_at", "orders", ["created_at"])
    op.create_index("ix_order_items_created_at", "order_items", ["created_at"])
    op.create_index(
        "ix_payment_gateway_configs_created_at", "payment_gateway_configs", ["created_at"]
    )
    op.create_index("ix_change_requests_created_at", "change_requests", ["created_at"])
    op.create_index("ix_price_book_created_at", "price_book", ["created_at"])


def downgrade() -> None:
    for table in (
        "price_book",
        "change_requests",
        "payment_gateway_configs",
        "order_items",
        "orders",
        "cart_items",
        "product_variants",
        "products",
        "product_categories",
    ):
        op.drop_table(table)

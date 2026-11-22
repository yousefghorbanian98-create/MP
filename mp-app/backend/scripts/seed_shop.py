"""دادهٔ اولیهٔ فروشگاه — دسته، محصول نمونه، دفتر قیمت، درگاه کارت‌به‌کارت.

قاعده: **idempotent**. اجرای دوباره چیزی را دوباره نمی‌سازد و قیمت‌های
دست‌کاری‌شده را بازنویسی نمی‌کند (فقط رکورد ناموجود می‌سازد).

استفاده:
    python scripts/seed_shop.py                # دادهٔ نمونه
    python scripts/seed_shop.py --dry-run      # فقط گزارش

دلیل وجود: صفحهٔ فروشگاه بدون داده «خراب» به نظر می‌رسد و ریویوورش فکر
می‌کند باگ است. تصاویر از `static/shop/` سرو می‌شوند (اگر نبودند، UI
placeholder نشان می‌دهد — عمداً تصویر جعلی از اینترنت نمی‌گذاریم).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from db.base import get_session_factory, init_db
from db.models import PaymentGatewayConfig, PriceBook, Product, ProductCategory

CATEGORIES = [
    {"slug": "supplements", "title": "مکمل‌ها", "kind": "supplement", "sort_order": 1},
    {"slug": "equipment", "title": "تجهیزات تمرین", "kind": "equipment", "sort_order": 2},
    {"slug": "apparel", "title": "پوشاک", "kind": "apparel", "sort_order": 3},
    {"slug": "services", "title": "خدمات باشگاه", "kind": "service", "sort_order": 4},
]

PRODUCTS = [
    {
        "sku": "WHEY-2KG",
        "title": "پروتئین وی ۲ کیلوگرمی",
        "subtitle": "۲۴ گرم پروتئین در هر پیمانه",
        "category_slug": "supplements",
        "price_rial": 2_900_000,
        "compare_at_rial": 3_400_000,
        "stock_qty": 12,
        "image_url": "/static/shop/whey.jpg",
    },
    {
        "sku": "CREATINE-300",
        "title": "کراتین مونوهیدرات ۳۰۰ گرم",
        "subtitle": "میکرونایز، بدون طعم",
        "category_slug": "supplements",
        "price_rial": 1_450_000,
        "stock_qty": 20,
        "image_url": "/static/shop/creatine.jpg",
    },
    {
        "sku": "SHAKER-MP",
        "title": "شیکر باشگاه MP",
        "subtitle": "۷۰۰ میلی‌لیتر، درپوش ضدچکه",
        "category_slug": "equipment",
        "price_rial": 350_000,
        "stock_qty": 30,
        "image_url": "/static/shop/shaker.jpg",
    },
    {
        "sku": "GLOVE-M-L",
        "title": "دستکش تمرین",
        "subtitle": "چرم مصنوعی با مچ‌بند",
        "category_slug": "equipment",
        "price_rial": 580_000,
        "stock_qty": 15,
        "image_url": "/static/shop/gloves.jpg",
    },
]

PRICES = [
    {
        "category": "membership",
        "code": "monthly",
        "title": "اشتراک ماهانه",
        "price_rial": 2_500_000,
        "duration_days": 30,
        "gender": "any",
    },
    {
        "category": "membership",
        "code": "quarterly",
        "title": "اشتراک سه‌ماهه",
        "price_rial": 6_300_000,
        "duration_days": 90,
        "gender": "any",
    },
    {
        "category": "coach_fee",
        "code": "pt-single",
        "title": "جلسهٔ مربی خصوصی",
        "price_rial": 900_000,
        "duration_days": None,
        "gender": "any",
    },
    {
        "category": "program_fee",
        "code": "program-8w",
        "title": "برنامهٔ ۸ هفته‌ای",
        "price_rial": 1_800_000,
        "duration_days": 56,
        "gender": "any",
    },
]

GATEWAY = {
    "kind": "card_to_card",
    "title": "کارت به کارت — بانک ملت",
    "card_number": "6104337712345678",
    "card_holder": "باشگاه ماسل پارادایس",
    "bank_name": "ملت",
    "instructions": "پس از واریز، شمارهٔ پیگیری را در اپ ثبت کنید.",
    "is_enabled": False,  # تا مالک شماره را تأیید نکند، فعال نیست
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    init_db()
    created = {"categories": 0, "products": 0, "prices": 0, "gateways": 0}
    with get_session_factory()() as db:
        slugs: dict[str, int] = {}
        for cat in CATEGORIES:
            row = db.scalar(select(ProductCategory).where(ProductCategory.slug == cat["slug"]))
            if row is None:
                if not args.dry_run:
                    row = ProductCategory(**cat)
                    db.add(row)
                    db.flush()
                created["categories"] += 1
            slugs[cat["slug"]] = getattr(row, "id", 0)

        for p in PRODUCTS:
            if db.scalar(select(Product).where(Product.sku == p["sku"])) is not None:
                continue
            if args.dry_run:
                created["products"] += 1
                continue
            category_id = slugs.get(p["category_slug"], 0)
            if not category_id:
                cat = db.scalar(
                    select(ProductCategory).where(ProductCategory.slug == p["category_slug"])
                )
                category_id = cat.id if cat else 0
            db.add(
                Product(
                    category_id=category_id,
                    sku=p["sku"],
                    title=p["title"],
                    subtitle=p.get("subtitle", ""),
                    description=p.get("description", ""),
                    price_rial=p["price_rial"],
                    compare_at_rial=p.get("compare_at_rial"),
                    image_url=p.get("image_url", ""),
                    stock_qty=p["stock_qty"],
                    is_active=True,
                    branch_id=1,
                )
            )
            created["products"] += 1

        for pr in PRICES:
            exists = db.scalar(
                select(PriceBook).where(
                    PriceBook.category == pr["category"], PriceBook.code == pr["code"]
                )
            )
            if exists is None:
                if not args.dry_run:
                    db.add(PriceBook(is_active=True, **pr))
                created["prices"] += 1

        if (
            db.scalar(
                select(PaymentGatewayConfig).where(PaymentGatewayConfig.kind == GATEWAY["kind"])
            )
            is None
        ):
            if not args.dry_run:
                db.add(PaymentGatewayConfig(**GATEWAY))
            created["gateways"] += 1

        if args.dry_run:
            print(f"[dry-run] will create: {created}")
            return 0
        db.commit()

    print(f"seed_shop: created {created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

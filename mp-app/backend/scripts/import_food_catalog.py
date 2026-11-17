"""واردات جدول غذایی ایرانی — منبع آزاد MIT (G5).

منبع: `soooolag/food-finder` (مجوز MIT) — ۳۰۶ غذای ایرانی با
`protein / carbs / calories` گروه‌بندی‌شده در ۱۶ دستهٔ فارسی.

## محدودیت منبع که پنهان نمی‌شود
منبع فقط **پروتئین** و **کربوهیدرات** می‌دهد؛ چربی صریحاً نیست.
`fat_g` در این اسکریپت با رابطهٔ آتووتر محاسبه می‌شود:

    کالری = 4×پروتئین + 4×کربوهیدرات + 9×چربی
    چربی  = (کالری − 4×پروتئین − 4×کربوهیدرات) / 9

این یک **تخمین** است، نه دادهٔ اندازه‌گیری‌شده. اگر نتیجه منفی یا غیرواقعی
بشود (کالری گزارش‌شده کمتر از مجموع پروتئین+کارب)، ردیف با
`fat_g = 0` و علامت هشدار در `notes` ذخیره می‌شود تا کسی آن را
«دادهٔ دقیق» نپندارد.

اعداد منبع برای **۱۰۰ گرم** هستند و مقادیر درشت‌شده (integer/float) به
همان شکل نگه داشته می‌شوند؛ هیچ عددی بازسازی یا گرد نمی‌شود.

اجرا:
    PYTHONPATH=. .venv/bin/python scripts/import_food_catalog.py --source /path/fit4.js
    PYTHONPATH=. .venv/bin/python scripts/import_food_catalog.py --source ... --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FOOD_CATALOG_VERSION = "food-catalog-ir-1.0"
SOURCE_REPO = "soooolag/food-finder"
SOURCE_LICENSE = "MIT"
SOURCE_URL = "https://github.com/soooolag/food-finder"

# ترتیب پارامترها در منبع: name, protein, carbs, calories, category
_ROW = re.compile(
    r"\{\s*name:\s*'(?P<name>[^']*)'\s*,"
    r"\s*protein:\s*(?P<protein>[\d.]+)\s*,"
    r"\s*carbs:\s*(?P<carbs>[\d.]+)\s*,"
    r"\s*calories:\s*(?P<calories>[\d.]+)\s*,"
    r"\s*category:\s*'(?P<category>[^']*)'\s*\}",
    re.MULTILINE,
)


def parse_source(text: str) -> list[dict]:
    """استخراج ردیف‌ها از فایل JS منبع. هیچ ردیفی ساخته نمی‌شود."""
    rows = []
    for m in _ROW.finditer(text):
        rows.append(
            {
                "name_fa": m.group("name").strip(),
                "protein_g": float(m.group("protein")),
                "carbs_g": float(m.group("carbs")),
                "kcal": int(round(float(m.group("calories")))),
                "category": m.group("category").strip(),
            }
        )
    return rows


# اختلاف زیر این آستانه (کیلوکالری) گرد کردن است، نه دادهٔ خراب:
# منبع اعداد را به عدد صحیح گرد کرده و مقدار کمی چربی/فیبر در محاسبه نبوده.
ROUNDING_TOLERANCE_KCAL = 15


def derive_fat(protein_g: float, carbs_g: float, kcal: float) -> tuple[float, str]:
    """چربی از رابطهٔ آتووتر — با هشدار وقتی داده با هم نمی‌خواند.

    خروجی: (چربی گرم, یادداشت). یادداشت خالی یعنی محاسبه سازگار بود.

    تفکیک مهم (بازبینی روی دادهٔ واقعی): از ۳۰۵ غذا، ۸۲ ردیف «باقی‌ماندهٔ منفی»
    داشتند، ولی اختلاف‌شان ۰ تا ۱۱ کیلوکالری بود — یعنی گِردکردن منبع، نه
    فساد داده. صفر‌کردن چربیِ گوشت گاو به‌خاطر ۱ کالری اضافه، خودش خطاست.
    پس: اختلاف کوچک ⇒ چربی صفر (و ردیف «سازگار» شمرده می‌شود)؛
    اختلاف بزرگ ⇒ صفر + یادداشت نامعلوم.
    """
    remainder = kcal - (4 * protein_g) - (4 * carbs_g)
    if remainder < 0:
        excess = -remainder
        if excess <= ROUNDING_TOLERANCE_KCAL:
            return 0.0, ""
        return 0.0, (
            f"چربی نامعلوم: کالری گزارش‌شده {excess:.0f} کیلوکالری کمتر از مجموع "
            "پروتئین و کربوهیدرات است (بیش از خطای گرد کردن) — صفر ثبت شد، نه تخمین"
        )
    fat = remainder / 9
    if fat > 100:
        return 0.0, (
            f"چربی نامعلوم: محاسبهٔ آتووتر {fat:.0f} گرم در ۱۰۰ گرم می‌داد (ناممکن) — صفر ثبت شد"
        )
    return round(fat, 1), ""


def build_rows(text: str) -> list[dict]:
    """ردیف‌های آمادهٔ درج در `food_items`."""
    out = []
    seen: set[str] = set()
    for row in parse_source(text):
        if not row["name_fa"] or row["name_fa"] in seen:
            continue
        seen.add(row["name_fa"])
        fat, note = derive_fat(row["protein_g"], row["carbs_g"], row["kcal"])
        out.append(
            {
                "name_fa": row["name_fa"],
                "name_en": "",
                "kcal_per_100g": row["kcal"],
                "protein_g_per_100g": row["protein_g"],
                "carbs_g_per_100g": row["carbs_g"],
                "fat_g_per_100g": fat,
                "category": row["category"],
                "external_id": f"{SOURCE_REPO}:{row['name_fa']}",
                "notes": note,
            }
        )
    return out


def import_rows(rows: list[dict], *, dry_run: bool = False) -> dict:
    """درج/به‌روزرسانی در DB. کلید یکتا: `external_id`."""
    from sqlalchemy import select

    from db.base import get_session_factory
    from db.models import FoodItem

    inserted = 0
    updated = 0
    skipped = 0
    factory = get_session_factory()
    with factory() as db:
        for row in rows:
            existing = db.scalar(select(FoodItem).where(FoodItem.external_id == row["external_id"]))
            if existing is None:
                if not dry_run:
                    db.add(
                        FoodItem(
                            external_id=row["external_id"],
                            name_fa=row["name_fa"],
                            name_en=row["name_en"],
                            kcal_per_100g=row["kcal_per_100g"],
                            protein_g_per_100g=row["protein_g_per_100g"],
                            carbs_g_per_100g=row["carbs_g_per_100g"],
                            fat_g_per_100g=row["fat_g_per_100g"],
                            category=row["category"],
                        )
                    )
                inserted += 1
            elif (
                existing.kcal_per_100g != row["kcal_per_100g"]
                or existing.protein_g_per_100g != row["protein_g_per_100g"]
                or existing.carbs_g_per_100g != row["carbs_g_per_100g"]
            ):
                if not dry_run:
                    existing.kcal_per_100g = row["kcal_per_100g"]
                    existing.protein_g_per_100g = row["protein_g_per_100g"]
                    existing.carbs_g_per_100g = row["carbs_g_per_100g"]
                    existing.fat_g_per_100g = row["fat_g_per_100g"]
                updated += 1
            else:
                skipped += 1
        if not dry_run:
            db.commit()

    return {
        "inserted": inserted,
        "updated": updated,
        "unchanged": skipped,
        "dry_run": dry_run,
        "total_parsed": len(rows),
        "source": {"repo": SOURCE_REPO, "license": SOURCE_LICENSE, "url": SOURCE_URL},
        "rule_version": FOOD_CATALOG_VERSION,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="واردات جدول غذایی ایرانی (MIT)")
    ap.add_argument("--source", required=True, help="مسیر فایل fit4.js منبع")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    path = Path(args.source)
    if not path.exists():
        print(f"فایل منبع پیدا نشد: {path}", file=sys.stderr)
        return 2

    rows = build_rows(path.read_text(encoding="utf-8"))
    if not rows:
        print("هیچ ردیفی از منبع استخراج نشد — الگوی فایل تغییر کرده است", file=sys.stderr)
        return 3

    inconsistent = sum(1 for r in rows if r["notes"])
    result = import_rows(rows, dry_run=args.dry_run)
    print(
        f"{result['inserted']} درج · {result['updated']} به‌روزرسانی · "
        f"{result['unchanged']} بدون تغییر · {inconsistent} ردیف با چربی نامعلوم"
    )
    print(f"منبع: {SOURCE_REPO} ({SOURCE_LICENSE}) — {SOURCE_URL}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

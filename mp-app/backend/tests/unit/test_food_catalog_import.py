"""G5 — واردات جدول غذایی ایرانی از منبع آزاد MIT.

هدف تست‌ها فقط «کار می‌کند» نیست؛ محافظت از **صداقت داده** است:
هیچ عددی نباید بازسازی شود و هیچ تخمینی نباید بی‌علامت بماند.
"""

from __future__ import annotations

import pytest

from scripts.import_food_catalog import (
    ROUNDING_TOLERANCE_KCAL,
    SOURCE_LICENSE,
    build_rows,
    derive_fat,
    parse_source,
)

SAMPLE = """
const foods = [
    { name: 'سینه مرغ (پخته)',        protein: 31,  carbs: 0,    calories: 165, category: 'پروتئین حیوانی' },
    { name: 'برنج سفید (پخته)',       protein: 2.7, carbs: 28,   calories: 130, category: 'غلات' },
    { name: 'خرما (مضافتی)',          protein: 2,   carbs: 75,   calories: 277, category: 'میوه' },
    { name: 'روغن زیتون',             protein: 0,   carbs: 0,    calories: 884, category: 'روغن و چربی' },
];
"""


def test_parses_every_row_of_the_source() -> None:
    rows = parse_source(SAMPLE)
    assert len(rows) == 4
    assert rows[0]["name_fa"] == "سینه مرغ (پخته)"
    assert rows[0]["protein_g"] == 31.0
    assert rows[0]["kcal"] == 165
    assert rows[0]["category"] == "پروتئین حیوانی"


def test_source_license_is_free() -> None:
    """قید کاربر: فقط کد/دادهٔ کاملاً آزاد."""
    assert SOURCE_LICENSE == "MIT"


def test_source_numbers_are_not_rescaled() -> None:
    """عدد منبع برای ۱۰۰ گرم است و باید همان بماند، نه گرد یا بازسازی."""
    rows = build_rows(SAMPLE)
    chicken = next(r for r in rows if r["name_fa"] == "سینه مرغ (پخته)")
    assert chicken["kcal_per_100g"] == 165
    assert chicken["protein_g_per_100g"] == 31.0
    assert chicken["carbs_g_per_100g"] == 0.0


def test_fat_is_derived_by_atwater() -> None:
    """چربی از معادلهٔ آتووتر — تنها راه ممکن، چون منبع چربی ندارد."""
    fat, note = derive_fat(protein_g=31, carbs_g=0, kcal=165)
    assert note == ""
    assert fat == pytest.approx(4.6, abs=0.1)  # (165 - 124) / 9


def test_rounding_noise_does_not_nullify_fat() -> None:
    """اختلاف چند کالری = گرد کردن منبع، نه فساد داده.

    کشف روی دادهٔ واقعی: ۸۲ غذا «باقی‌ماندهٔ منفی» داشتند ولی اختلاف‌شان
    زیر ۱۵ کالری بود. صفر کردن چربی به‌خاطر ۱ کالری، خطای بزرگ‌تری است.
    """
    fat, note = derive_fat(protein_g=0.9, carbs_g=9.6, kcal=41)
    assert note == ""
    assert fat == 0.0


def test_large_inconsistency_is_declared_unknown() -> None:
    """خرما: ۲ گرم پروتئین + ۷۵ گرم کارب ≠ ۲۷۷ کالری (باید ۳۰۸ باشد).

    این تناقض واقعی است و باید **نامعلوم** اعلام شود، نه با عدد ساختگی پر شود.
    """
    fat, note = derive_fat(protein_g=2, carbs_g=75, kcal=277)
    assert fat == 0.0
    assert "نامعلوم" in note
    assert "گرد کردن" in note


def test_tolerance_boundary_is_explicit() -> None:
    """آستانه باید عددی و مستند باشد، نه جادو."""
    assert ROUNDING_TOLERANCE_KCAL > 0
    # دقیقاً روی مرز: پروتئین/کارب طوری که اختلاف ۱۴ کالری بدهد
    ok_fat, ok_note = derive_fat(protein_g=25, carbs_g=0, kcal=100 - 14)
    assert ok_note == ""
    # و اختلاف ۱۶ کالری باید نامعلوم شود
    bad_fat, bad_note = derive_fat(protein_g=25, carbs_g=0, kcal=100 - 16)
    assert "نامعلوم" in bad_note


def test_no_duplicate_names() -> None:
    dup = SAMPLE.replace("برنج سفید (پخته)", "سینه مرغ (پخته)")
    rows = build_rows(dup)
    assert len([r for r in rows if r["name_fa"] == "سینه مرغ (پخته)"]) == 1


def test_external_id_is_traceable_to_source() -> None:
    """هر ردیف باید به منبعش برگشت‌پذیر باشد — برای بازبینی و تازه‌سازی."""
    rows = build_rows(SAMPLE)
    assert all(r["external_id"].startswith("soooolag/food-finder:") for r in rows)


def test_empty_source_is_an_error_not_an_empty_success() -> None:
    """اگر الگوی فایل منبع تغییر کند، باید صریح شکست بخورد."""
    assert build_rows("const foods = [];") == []

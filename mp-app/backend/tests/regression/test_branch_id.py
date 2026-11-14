"""تست رگریشن R-001 — وجود branch_id در همهٔ جدول‌های اصلی.

باگ/دام M03 (لایهٔ ۳): فراموشی branch_id و دردسر مهاجرت بعدی.
هرگز جدول اصلی جدید بدون branch_id ساخته نشود — این تست آن را مکانیکی می‌کند.
"""

from __future__ import annotations

from db.base import Base

# فهرست جدول‌های اصلی «چندشعبه‌پذیر» — با افزودن جدول جدید، اینجا هم اضافه شود
BRANCH_SCOPED_TABLES = {
    "members",
    "memberships",
    "payments",
    "wallet_transactions",
    "assessments",
    "jackson_pollock_measurements",
    "face_templates",
    "checkins",
    "workout_programs",
    "nutrition_plans",
    "campaigns",
    "offers",
}


def test_regression_branch_id_present_on_all_main_tables():
    for table in sorted(BRANCH_SCOPED_TABLES):
        t = Base.metadata.tables[table]
        assert "branch_id" in {c.name for c in t.columns}, (
            f"REGRESSION R-001: جدول {table} branch_id ندارد"
        )


def test_regression_branch_id_indexed():
    for table in sorted(BRANCH_SCOPED_TABLES):
        col = Base.metadata.tables[table].columns["branch_id"]
        assert col.index, f"REGRESSION R-001: branch_id در {table} ایندکس ندارد"

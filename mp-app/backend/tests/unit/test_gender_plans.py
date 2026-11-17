"""تست‌های موتور پلن جنسیت‌محور (M41-c2) — قاعدهٔ ۳۷ روز + reason + نسخهٔ سیاست."""

from __future__ import annotations

import pytest

from engine.gender_plans import (
    MENSTRUAL_RECOVERY_DAYS,
    PLAN_POLICY_VERSION,
    WOMEN_MONTH_REASON,
    list_plans,
    resolve_plan,
    women_month_days,
)


def test_women_month_is_37_days_by_rule() -> None:
    """قاعده: ۳۰ + ۷ — محاسباتی، نه hardcode."""
    assert women_month_days() == 37
    assert women_month_days() == 30 + MENSTRUAL_RECOVERY_DAYS


def test_female_plan_has_37_days_and_policy_reason() -> None:
    result = resolve_plan(plan_key="monthly_basic", gender="female")
    assert result["duration_days"] == 37
    assert result["plan_name"] == "ماهانهٔ بانوان — پایه"
    assert result["reason"] == WOMEN_MONTH_REASON
    assert "۳۷" in result["reason"]
    assert result["policy_version"] == PLAN_POLICY_VERSION


def test_male_plan_has_30_days_and_different_price() -> None:
    male = resolve_plan(plan_key="monthly_basic", gender="male")
    female = resolve_plan(plan_key="monthly_basic", gender="female")
    assert male["duration_days"] == 30
    assert male["reason"] != female["reason"]
    assert male["price_rial"] != female["price_rial"]  # قیمت/شرایط متفاوت (تصمیم مالک)


def test_quarterly_male_90_days_female_111() -> None:
    male = resolve_plan(plan_key="quarterly", gender="male")
    female = resolve_plan(plan_key="quarterly", gender="female")
    assert male["duration_days"] == 90
    assert female["duration_days"] == 3 * 37  # هر ماه بانوان = ۳۷ روز


def test_unknown_plan_or_gender_fails_loudly() -> None:
    with pytest.raises(KeyError):
        resolve_plan(plan_key="vip", gender="male")
    with pytest.raises(ValueError, match="جنسیت"):
        resolve_plan(plan_key="monthly_basic", gender="unknown")


def test_list_plans_covers_both_genders() -> None:
    plans = list_plans()
    assert len(plans) == 6  # ۳ پلن × ۲ جنسیت
    assert {p["gender"] for p in plans} == {"male", "female"}
    assert all(p["reason"] for p in plans)

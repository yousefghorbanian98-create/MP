"""تست‌های موتور امتیازدهی (M35-c2) — درون‌یابی، بستن لبه، جدول ناقص، SDC."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from engine.scoring import SCORE_VERSION, estimate_percentile, is_real_change, score_test

PUSHUP_M_2029 = {"5": 8, "25": 22, "50": 25, "75": 29, "95": 40}
REACH_M_3034 = {"25": 15.3, "75": 32.9}  # جدول ناقص (فقط ۲۵/۷۵)


def test_exact_on_documented_point() -> None:
    est = estimate_percentile(raw_value=25, percentiles=PUSHUP_M_2029)
    assert est == {"percentile": 50.0, "quality": "exact"}


def test_interpolation_between_points() -> None:
    # بین ۲۵ (22) و ۵۰ (25): مقدار 23.5 ← درصدک 37.5
    est = estimate_percentile(raw_value=23.5, percentiles=PUSHUP_M_2029)
    assert est["percentile"] == 37.5
    assert est["quality"] == "interpolated"


def test_clamping_outside_table() -> None:
    low = estimate_percentile(raw_value=2, percentiles=PUSHUP_M_2029)
    high = estimate_percentile(raw_value=90, percentiles=PUSHUP_M_2029)
    assert low == {"percentile": 1.0, "quality": "clamped"}
    assert high == {"percentile": 99.0, "quality": "clamped"}


def test_sparse_table_gives_range_estimate() -> None:
    est = estimate_percentile(raw_value=24, percentiles=REACH_M_3034)
    assert est["quality"] == "range_estimate"
    assert 25 < est["percentile"] < 75
    edge = estimate_percentile(raw_value=10, percentiles=REACH_M_3034)
    assert edge == {"percentile": 5.0, "quality": "range_estimate"}


def test_lower_better_direction() -> None:
    # دویدن: زمان کمتر ← نمرهٔ عملکرد بالاتر (وارون درصدک توزیع زمان)
    table = {"25": 400.0, "75": 300.0}  # ثانیه: صدک ۲۵ توزیع زمان = 400
    fast = estimate_percentile(raw_value=300, percentiles=table, direction="lower_better")
    assert fast == {"percentile": 25.0, "quality": "range_estimate"}  # 100 - 75
    slow = estimate_percentile(raw_value=400, percentiles=table, direction="lower_better")
    assert slow == {"percentile": 75.0, "quality": "range_estimate"}  # 100 - 25
    mid = estimate_percentile(raw_value=350, percentiles=table, direction="lower_better")
    assert mid["percentile"] == 50.0


def test_score_test_carries_reason_and_version() -> None:
    norm = {
        "test_key": "pushup_1min",
        "sex": "m",
        "age_min": 20,
        "age_max": 29,
        "percentiles": PUSHUP_M_2029,
        "source": "https://fitnessnorms.com/strength/push-ups/",
    }
    result = score_test(raw_value=25, norm=norm)
    assert result["score"] == 50.0
    assert result["reason"]
    assert result["rule_version"] == SCORE_VERSION


def test_sdc_gate() -> None:
    noise = is_real_change(old_value=20, new_value=22, sdc=9.0)
    assert noise["real_change"] is False
    assert "نویز" in noise["reason"]
    real = is_real_change(old_value=20, new_value=30, sdc=9.0)
    assert real["real_change"] is True
    unknown = is_real_change(old_value=20, new_value=30, sdc=None)
    assert unknown["real_change"] is None
    assert "نامعلوم" in unknown["reason"]


def test_invalid_inputs_fail_loudly() -> None:
    with pytest.raises(ApiError, match="نامعلوم"):
        estimate_percentile(raw_value=None, percentiles=PUSHUP_M_2029)
    with pytest.raises(ApiError, match="خالی"):
        estimate_percentile(raw_value=5, percentiles={})
    with pytest.raises(ApiError, match="نامعتبر"):
        estimate_percentile(raw_value=5, percentiles={"50": 3, "90": 4})
    with pytest.raises(ApiError, match="فاقد"):
        score_test(raw_value=5, norm={"test_key": "x"})

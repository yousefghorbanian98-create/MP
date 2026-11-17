"""G3 — تغذیهٔ سازگار: TDEE از روند وزن واقعی.

روش تست: **آزمون زمینِ معلوم**. یک سناریوی مصنوعی با TDEE واقعیِ مشخص
می‌سازیم و می‌بینیم موتور همان عدد را برمی‌گرداند یا نه. اگر تست فقط
«خروجی عددی است» را بسنجد، یک باگ ۳۰٪ در برآورد شیب (که واقعاً رخ داد)
را نمی‌گیرد.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from engine.adaptive_nutrition import (
    KCAL_PER_KG,
    MAX_STEP_RATIO,
    MIN_INTAKE_DAYS,
    MIN_WEIGHT_DAYS,
    SAFE_GAIN_PCT_PER_WEEK,
    SAFE_LOSS_PCT_PER_WEEK,
    ema_weights,
    estimate_tdee,
    suggest_calorie_adjustment,
    weight_trend,
)


def _series(start_weight: float, slope_kg_week: float, days: int = 28, start: date | None = None):
    """وزن روزانهٔ مصنوعی با شیب دقیقِ معلوم."""
    start = start or date(2026, 10, 18)
    return [
        ((start + timedelta(days=i)).isoformat(), round(start_weight + slope_kg_week * (i / 7), 2))
        for i in range(days)
    ]


# ── روند وزن ──


@pytest.mark.parametrize("true_slope", [-0.5, -0.2, 0.0, 0.25, 0.4])
def test_slope_is_recovered_exactly(true_slope: float) -> None:
    """شیب تزریق‌شده باید عیناً برگردد.

    کشف واقعی: نسخهٔ اول رگرسیون را روی وزن EMA صاف‌شده می‌گرفت و
    −۰٫۵ را −۰٫۳۵ برمی‌گرداند (کم‌برآورد ۳۰٪) چون EMA در ابتدای بازه
    عقب است. OLS روی دادهٔ خام این خطای سیستماتیک را ندارد.
    """
    t = weight_trend(_series(80.0, true_slope))
    assert t.slope_kg_per_week == pytest.approx(true_slope, abs=0.01)


def test_slope_ignores_water_noise() -> None:
    """نوسان آب/گلیکوژن نباید روند را جابه‌جا کند."""
    pts = _series(80.0, -0.4, days=28)
    noisy = [(d, round(w + (0.6 if i % 2 == 0 else -0.6), 2)) for i, (d, w) in enumerate(pts)]
    t = weight_trend(noisy)
    assert t.slope_kg_per_week == pytest.approx(-0.4, abs=0.15)


def test_too_few_measurements_is_insufficient_not_zero() -> None:
    """کمتر از حد لازم ⇒ «نمی‌دانم»، نه شیب صفر."""
    t = weight_trend(_series(80.0, -0.5, days=MIN_WEIGHT_DAYS - 1))
    assert t.slope_kg_per_week is None
    assert t.confidence == "insufficient"
    assert "حداقل" in t.reason


def test_short_span_is_insufficient() -> None:
    """۱۴ اندازه‌گیری در ۵ روز (وزن‌کشی چندبار در روز) روند نیست."""
    start = date(2026, 10, 18)
    pts = [((start + timedelta(days=i // 3)).isoformat(), 80.0 - i * 0.01) for i in range(15)]
    t = weight_trend(pts)
    assert t.slope_kg_per_week is None
    assert "بازهٔ اندازه‌گیری" in t.reason


def test_confidence_grows_with_span() -> None:
    short = weight_trend(_series(80.0, -0.3, days=18))
    long = weight_trend(_series(80.0, -0.3, days=35))
    order = {"insufficient": 0, "low": 1, "medium": 2, "high": 3}
    assert order[long.confidence] >= order[short.confidence]


def test_noisy_data_reports_low_confidence_and_warns() -> None:
    pts = _series(80.0, -0.2, days=16)
    jittered = [(d, round(w + (1.8 if i % 3 == 0 else -1.5), 2)) for i, (d, w) in enumerate(pts)]
    t = weight_trend(jittered)
    assert t.confidence in ("low", "insufficient")


def test_ema_smooths_toward_recent_values() -> None:
    """EMA باید به مقدار اخیر وزن بیشتری بدهد (خاصیت نیمه‌عمر)."""
    pts = [("2026-11-01", 80.0), ("2026-11-02", 80.0), ("2026-11-10", 84.0)]
    smoothed = ema_weights(pts)
    assert smoothed[-1][1] > 81.0  # به ۸۴ نزدیک شده، نه میانگین سادهٔ ۸۱٫۳
    assert smoothed[-1][1] < 84.0


# ── TDEE ──


def test_tdee_recovers_known_ground_truth() -> None:
    """سناریوی کنترل‌شده: مصرف ۲۱۰۰، کاهش ۰٫۵ کیلو در هفته ⇒ TDEE ≈ ۲۶۵۰.

    محاسبه: ۰٫۵ × ۷۷۰۰ / ۷ = ۵۵۰ کالری کسری روزانه ⇒ ۲۱۰۰ + ۵۵۰ = ۲۶۵۰
    """
    pts = _series(80.0, -0.5, days=28)
    intake = {d: 2100.0 for d, _ in pts}

    est = estimate_tdee(weight_points=pts, intake_by_date=intake)

    assert est["data_state"] == "estimated"
    assert est["tdee_kcal"] == pytest.approx(2650, abs=25)
    assert est["confidence"] in ("medium", "high")


def test_tdee_recovers_gain_scenario() -> None:
    """افزایش وزن ⇒ TDEE پایین‌تر از مصرف است، نه بالاتر."""
    pts = _series(70.0, 0.25, days=28)
    intake = {d: 3000.0 for d, _ in pts}

    est = estimate_tdee(weight_points=pts, intake_by_date=intake)

    # ۰٫۲۵ × ۷۷۰۰ / ۷ ≈ ۲۷۵ کالری مازاد روزانه ⇒ TDEE ≈ ۲۷۲۵
    assert est["tdee_kcal"] == pytest.approx(3000 - (0.25 * KCAL_PER_KG / 7), abs=25)


def test_unlogged_days_are_not_counted_as_zero() -> None:
    """بزرگ‌ترین منبع خطا در اپ‌های تغذیه: روز ثبت‌نشده = صفر کالری.

    اگر روزهای ثبت‌نشده صفر حساب شوند، میانگین مصرف مصنوعی پایین می‌آید و
    TDEE هم پایین برآورد می‌شود — دقیقاً برعکس آنچه باید.
    """
    pts = _series(80.0, -0.5, days=28)
    partial = {d: 2100.0 for d, _ in pts[:10]}
    partial.update({d: 0.0 for d, _ in pts[10:]})  # صفرِ «ثبت نشده»

    est = estimate_tdee(weight_points=pts, intake_by_date=partial)

    assert est["mean_intake_kcal"] == pytest.approx(2100, abs=1)
    assert est["tdee_kcal"] == pytest.approx(2650, abs=25)


def test_insufficient_intake_blocks_estimation() -> None:
    pts = _series(80.0, -0.5, days=28)
    intake = {d: 2000.0 for d, _ in pts[: MIN_INTAKE_DAYS - 1]}

    est = estimate_tdee(weight_points=pts, intake_by_date=intake)

    assert est["tdee_kcal"] is None
    assert est["data_state"] == "insufficient_intake"
    assert "حداقل" in est["reason"]


def test_insufficient_weight_blocks_estimation() -> None:
    intake = {(date(2026, 10, 18) + timedelta(days=i)).isoformat(): 2000.0 for i in range(14)}
    est = estimate_tdee(weight_points=_series(80.0, -0.5, days=5), intake_by_date=intake)

    assert est["tdee_kcal"] is None
    assert est["data_state"] == "insufficient_weight"


def test_estimate_carries_assumptions_and_source() -> None:
    """هیچ عددی بدون منبع و فرض نمی‌ماند."""
    pts = _series(80.0, -0.4, days=28)
    est = estimate_tdee(weight_points=pts, intake_by_date={d: 2200.0 for d, _ in pts})

    assert est["rule_version"] == "adaptive-nutrition-1.0"
    assert est["assumptions"]
    assert any("7700" in a or "کیلوگرم" in a for a in est["assumptions"])


# ── اصلاح کالری ──


def test_adjustment_is_capped_per_week() -> None:
    """حتی با اختلاف بزرگ، یک هفته بیش از ۱۵٪ جابه‌جا نمی‌شود."""
    adj = suggest_calorie_adjustment(
        tdee_kcal=3500,
        current_target_kcal=2000,
        goal="hypertrophy",
        body_weight_kg=80,
        slope_kg_per_week=0.0,
    )
    assert adj["action"] == "increase"
    assert adj["capped"] is True
    assert adj["suggested_target_kcal"] == pytest.approx(2000 * (1 + MAX_STEP_RATIO), abs=1)


def test_no_change_when_target_already_matches() -> None:
    adj = suggest_calorie_adjustment(
        tdee_kcal=2500,
        current_target_kcal=2500,
        goal="fitness",
        body_weight_kg=80,
        slope_kg_per_week=0.0,
    )
    assert adj["action"] == "keep"
    assert adj["delta_kcal"] == 0


def test_too_fast_loss_increases_calories_first() -> None:
    """روند ۱٫۵٪ در هفته = تحلیل عضله. اول روند اصلاح می‌شود، نه کسری بیشتر."""
    adj = suggest_calorie_adjustment(
        tdee_kcal=2600,
        current_target_kcal=1800,
        goal="weight_loss",
        body_weight_kg=80,
        slope_kg_per_week=-1.2,  # ۱٫۵٪ در هفته
    )
    assert adj["action"] == "increase"
    assert "تحلیل عضله" in adj["reason"]
    assert SAFE_LOSS_PCT_PER_WEEK == 1.0


def test_too_fast_gain_decreases_calories() -> None:
    adj = suggest_calorie_adjustment(
        tdee_kcal=3000,
        current_target_kcal=3500,
        goal="hypertrophy",
        body_weight_kg=80,
        slope_kg_per_week=0.8,  # ۱٪ در هفته
    )
    assert adj["action"] == "decrease"
    assert "چربی" in adj["reason"]
    assert SAFE_GAIN_PCT_PER_WEEK == 0.5


def test_missing_tdee_makes_no_suggestion() -> None:
    adj = suggest_calorie_adjustment(
        tdee_kcal=None,
        current_target_kcal=2000,
        goal="weight_loss",
        body_weight_kg=80,
        slope_kg_per_week=None,
    )
    assert adj["action"] == "none"
    assert adj["delta_kcal"] == 0


def test_unknown_goal_changes_nothing() -> None:
    adj = suggest_calorie_adjustment(
        tdee_kcal=2600,
        current_target_kcal=2000,
        goal="bulking_extreme",
        body_weight_kg=80,
        slope_kg_per_week=0.0,
    )
    assert adj["action"] == "none"
    assert "جدول قواعد نیست" in adj["reason"]


def test_end_to_end_chain_from_data_to_suggestion() -> None:
    """زنجیرهٔ کامل: وزن + غذا ⇒ TDEE ⇒ پیشنهاد، همه از دادهٔ یکسان."""
    pts = _series(85.0, -0.55, days=35)
    intake = {d: 2000.0 for d, _ in pts}

    est = estimate_tdee(weight_points=pts, intake_by_date=intake)
    adj = suggest_calorie_adjustment(
        tdee_kcal=est["tdee_kcal"],
        current_target_kcal=2000,
        goal="weight_loss",
        body_weight_kg=82.0,
        slope_kg_per_week=est["trend"]["slope_kg_per_week"],
    )

    assert est["tdee_kcal"] == pytest.approx(2000 + 0.55 * KCAL_PER_KG / 7, abs=30)
    # ۰٫۵۵ کیلو در هفته روی ۸۲ کیلو = ۰٫۶۷٪ — زیر مرز ۱٪، پس اصلاح گام‌دار
    assert adj["action"] in ("increase", "keep")
    assert adj["rule_version"] == "adaptive-nutrition-1.0"

"""M54-c1 — آنالیز سگمنتال آنتروپومتریک (segmental-1.0).

قاعدهٔ محافظت‌شده: **هیچ شاخصی با دادهٔ ناقص ساخته نمی‌شود.** پر کردن
محیط اندازه‌گیری‌نشده با صفر، فرد را «نامتقارن» یا «چاق» نشان می‌دهد.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from engine.segmental import (
    ASYMMETRY_THRESHOLD_CM,
    SEGMENTAL_VERSION,
    analyze,
    trend,
)


def full(**over) -> dict:
    base = {
        "waist_cm": 88.0,
        "hip_cm": 100.0,
        "chest_cm": 102.0,
        "neck_cm": 39.0,
        "upper_arm_right_cm": 34.0,
        "upper_arm_left_cm": 34.2,
        "thigh_right_cm": 58.0,
        "thigh_left_cm": 58.4,
        "calf_right_cm": 38.0,
        "calf_left_cm": 38.1,
    }
    base.update(over)
    return base


class TestRatios:
    def test_waist_to_height_normal(self) -> None:
        r = analyze(full(), height_cm=178, gender="male")
        w = r["ratios"]["waist_to_height"]
        assert w["value"] == 0.494
        assert w["band"] == "normal"

    def test_waist_to_height_elevated(self) -> None:
        r = analyze(full(waist_cm=100.0), height_cm=178, gender="male")
        assert r["ratios"]["waist_to_height"]["band"] == "elevated"

    def test_waist_to_height_unknown_without_height(self) -> None:
        r = analyze(full(), height_cm=None, gender="male")
        assert r["ratios"]["waist_to_height"]["value"] is None
        assert r["ratios"]["waist_to_height"]["band"] == "unknown"
        assert "whtr" in r["missing"]

    def test_waist_to_hip_threshold_depends_on_gender(self) -> None:
        m = analyze(full(waist_cm=88.0, hip_cm=100.0), height_cm=178, gender="male")
        # 0.88 زیر آستانهٔ مرد (0.90) اما بالای آستانهٔ زن (0.85)
        assert m["ratios"]["waist_to_hip"]["band"] == "normal"
        f = analyze(full(waist_cm=88.0, hip_cm=100.0), height_cm=170, gender="female")
        assert f["ratios"]["waist_to_hip"]["band"] == "high"

    def test_hip_zero_does_not_crash_or_invent(self) -> None:
        r = analyze(full(hip_cm=0.0), height_cm=178, gender="male")
        assert r["ratios"]["waist_to_hip"]["value"] is None
        assert "whr" in r["missing"]

    def test_arm_to_waist_low_is_flagged(self) -> None:
        r = analyze(full(upper_arm_right_cm=28.0, waist_cm=95.0), height_cm=178, gender="male")
        assert r["ratios"]["arm_to_waist"]["band"] == "low"

    def test_arm_to_waist_falls_back_to_left_arm(self) -> None:
        r = analyze(
            full(upper_arm_right_cm=None, upper_arm_left_cm=34.0), height_cm=178, gender="male"
        )
        assert r["ratios"]["arm_to_waist"]["value"] is not None
        assert r["ratios"]["arm_to_waist"]["value"] == round(34.0 / 88.0, 3)


class TestAsymmetry:
    def test_small_difference_is_normal(self) -> None:
        r = analyze(full(), height_cm=178, gender="male")
        a = r["asymmetry"]["upper_arm"]
        assert a["band"] == "normal"
        # راست ۳۴٫۰ و چپ ۳۴٫۲ ⇒ دلتا ۰٫۲- (سمت چپ بزرگ‌تر)
        assert abs(a["delta_cm"] - -0.2) < 0.001
        assert a["dominant_side"] == "left"

    def test_mild_difference(self) -> None:
        r = analyze(
            full(upper_arm_right_cm=35.5, upper_arm_left_cm=34.0), height_cm=178, gender="male"
        )
        assert r["asymmetry"]["upper_arm"]["band"] == "mild"

    def test_notable_asymmetry_sets_headline(self) -> None:
        r = analyze(
            full(upper_arm_right_cm=37.0, upper_arm_left_cm=34.0), height_cm=178, gender="male"
        )
        assert r["asymmetry"]["upper_arm"]["band"] == "notable"
        assert r["asymmetry"]["upper_arm"]["dominant_side"] == "right"
        assert "upper_arm" in r["headline"]

    def test_one_sided_measurement_makes_no_claim(self) -> None:
        r = analyze(full(upper_arm_left_cm=None), height_cm=178, gender="male")
        assert r["asymmetry"]["upper_arm"] is None
        assert r["asymmetry"]["thigh"] is not None

    def test_all_one_sided_uses_honest_headline(self) -> None:
        r = analyze(
            full(upper_arm_left_cm=None, thigh_left_cm=None, calf_left_cm=None),
            height_cm=178,
            gender="male",
        )
        assert "هر دو سمت" in r["headline"]

    def test_threshold_constant_is_documented(self) -> None:
        assert ASYMMETRY_THRESHOLD_CM == 1.0


class TestHonesty:
    def test_note_never_claims_body_composition(self) -> None:
        r = analyze(full(), height_cm=178, gender="male")
        assert "InBody" in r["note"]
        assert "نه ترکیب بدنی" in r["note"] or "آنتروپومتریک" in r["note"]

    def test_rule_version_is_reported(self) -> None:
        assert analyze(full(), height_cm=178, gender="male")["rule_version"] == SEGMENTAL_VERSION

    def test_empty_measurement_makes_no_false_claims(self) -> None:
        r = analyze({}, height_cm=None, gender=None)
        assert r["ratios"]["waist_to_height"]["value"] is None
        assert r["ratios"]["waist_to_hip"]["value"] is None
        assert r["ratios"]["arm_to_waist"]["value"] is None
        assert set(r["missing"]) == {"whtr", "whr", "arm_to_waist"}


class TestTrend:
    def _p(self, days_ago: int, **kw) -> dict:
        base = {"measured_at": datetime.now(UTC) - timedelta(days=days_ago)}
        base.update(kw)
        return base

    def test_single_point_is_not_a_trend(self) -> None:
        assert trend([self._p(10, waist_cm=90)]) is None

    def test_empty_is_not_a_trend(self) -> None:
        assert trend([]) is None

    def test_waist_reduction_is_reported(self) -> None:
        t = trend([self._p(60, waist_cm=95.0), self._p(0, waist_cm=89.0)])
        assert t is not None
        assert t["changes_cm"]["waist_cm"] == -6.0
        assert t["biggest_change"] == "waist_cm"
        assert "کاهش ۶" in t["headline"] or "کاهش 6" in t["headline"]
        assert t["span_days"] == 60

    def test_small_change_is_called_noise(self) -> None:
        t = trend([self._p(30, waist_cm=90.0), self._p(0, waist_cm=90.8)])
        assert t is not None
        assert "نوسان" in t["headline"]

    def test_missing_site_in_one_point_is_skipped_not_zeroed(self) -> None:
        t = trend(
            [self._p(30, waist_cm=90.0, chest_cm=None), self._p(0, waist_cm=88.0, chest_cm=104.0)]
        )
        assert t is not None
        assert t["changes_cm"]["chest_cm"] is None

    def test_no_common_metric_gives_honest_headline(self) -> None:
        t = trend([self._p(30, neck_cm=40.0), self._p(0, neck_cm=39.0)])
        assert t is not None
        assert "مشترک نیست" in t["headline"]
        assert t["biggest_change"] is None

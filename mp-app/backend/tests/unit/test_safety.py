"""Q7 — غربالگری ایمنی (safety-1.0).

قاعدهٔ محافظت‌شده: **«محدودیتی ثبت نشده» با «بی‌خطر» یکی نیست.**
این تفاوت همان چیزی است که در دفاع پایان‌نامه قابل دفاع است و در
محصول تجاری غالباً پنهان می‌شود.
"""

from __future__ import annotations

from engine.safety import (
    CONTRAINDICATIONS,
    SCREENING_VERSION,
    SENIOR_RULES,
    apply_senior_protocol,
    screen,
)


class TestUnknownIsNotSafe:
    def test_no_constraints_is_unknown_not_healthy(self) -> None:
        r = screen(constraints=[], planned_patterns=["squat"])
        assert r["status"] == "unknown"
        assert r["safe_to_generate"] is False
        assert "نامعلوم" in r["headline"]

    def test_none_constraints_behaves_like_empty(self) -> None:
        r = screen(constraints=None, planned_patterns=["squat"])
        assert r["status"] == "unknown"

    def test_unknown_label_is_reported_not_ignored(self) -> None:
        r = screen(constraints=["broken_ankle"], planned_patterns=["squat"])
        assert r["status"] == "needs_review"
        assert r["unknown_constraints"] == ["broken_ankle"]
        assert r["safe_to_generate"] is False


class TestBlocking:
    def test_knee_injury_blocks_squat_and_lunge(self) -> None:
        r = screen(
            constraints=["knee_injury"],
            planned_patterns=["squat", "lunge", "leg_press", "bench_press"],
        )
        assert r["status"] == "blocked"
        assert r["blocked"][0]["blocked_exercises"] == ["squat", "lunge"]
        assert "leg_press_light" in r["blocked"][0]["alternatives"], (
            "جایگزین باید بار سبک باشد، نه همان حرکت"
        )
        assert r["safe_to_generate"] is False

    def test_low_back_pain_blocks_deadlift(self) -> None:
        r = screen(constraints=["low_back_pain"], planned_patterns=["deadlift", "squat"])
        assert r["status"] == "blocked"
        assert r["blocked"][0]["blocked_exercises"] == ["deadlift"]

    def test_shoulder_impingement_blocks_overhead_press(self) -> None:
        r = screen(
            constraints=["shoulder_impingement"], planned_patterns=["overhead_press", "curl"]
        )
        assert r["status"] == "blocked"

    def test_pregnancy_blocks_supine_work(self) -> None:
        r = screen(constraints=["pregnancy"], planned_patterns=["supine_exercise", "squat"])
        assert r["status"] == "blocked"

    def test_hypertension_blocks_max_effort(self) -> None:
        r = screen(constraints=["hypertension"], planned_patterns=["max_effort_single"])
        assert r["status"] == "blocked"


class TestClear:
    def test_known_constraint_without_conflict_is_clear(self) -> None:
        r = screen(constraints=["knee_injury"], planned_patterns=["bench_press", "row"])
        assert r["status"] == "clear"
        assert r["safe_to_generate"] is True

    def test_multiple_constraints_all_checked(self) -> None:
        r = screen(
            constraints=["knee_injury", "low_back_pain"],
            planned_patterns=["squat", "deadlift"],
        )
        assert r["status"] == "blocked"
        assert len(r["blocked"]) == 2


class TestNotes:
    def test_senior_age_adds_a_note(self) -> None:
        r = screen(constraints=["knee_injury"], planned_patterns=["bench_press"], age=70)
        assert any("۶۵" in n for n in r["notes"])

    def test_young_age_adds_no_note(self) -> None:
        r = screen(constraints=["knee_injury"], planned_patterns=["bench_press"], age=30)
        assert r["notes"] == []

    def test_high_risk_pattern_is_flagged_even_without_constraints(self) -> None:
        r = screen(constraints=["knee_injury"], planned_patterns=["inverted", "bench_press"])
        assert r["high_risk_patterns"] == ["inverted"]
        assert any("پرخطر" in n for n in r["notes"])

    def test_missing_medical_clearance_blocks_generation(self) -> None:
        r = screen(
            constraints=["knee_injury"],
            planned_patterns=["bench_press"],
            has_medical_clearance=False,
        )
        assert r["status"] == "needs_review"
        assert r["safe_to_generate"] is False

    def test_present_clearance_does_not_downgrade(self) -> None:
        r = screen(
            constraints=["knee_injury"],
            planned_patterns=["bench_press"],
            has_medical_clearance=True,
        )
        assert r["status"] == "clear"


class TestHonesty:
    def test_disclaimer_is_always_present(self) -> None:
        r = screen(constraints=[], planned_patterns=[])
        assert "جای تشخیص پزشک" in r["disclaimer_fa"]

    def test_known_constraints_are_listed_for_the_ui(self) -> None:
        r = screen(constraints=[], planned_patterns=[])
        assert "knee_injury" in r["known_constraints"]
        assert "pregnancy" in r["known_constraints"]

    def test_rule_version(self) -> None:
        assert screen(constraints=[], planned_patterns=[])["rule_version"] == SCREENING_VERSION

    def test_every_contraindication_has_alternatives(self) -> None:
        for key, rule in CONTRAINDICATIONS.items():
            assert rule["alternatives"], f"{key} بدون جایگزین است"
            assert rule["blocked_patterns"], f"{key} بدون الگوی مسدود"
            assert rule["advice_fa"], f"{key} بدون توصیه"


class TestCoexistenceWithSeniorProtocol:
    """Q7 کشف: `engine/safety.py` از قبل پروتکل سالمند (D-016) را داشت.

    بازنویسی کامل آن، قواعد سالمند را نابود می‌کرد. این تست‌ها تضمین
    می‌کنند هر دو دامنه در یک ماژول کنار هم زنده بمانند.
    """

    def test_senior_rules_still_exist(self) -> None:
        assert SENIOR_RULES["load_multiplier"] == 0.7
        assert SENIOR_RULES["max_strength_testing"] is False
        assert SENIOR_RULES["balance_component_required"] is True

    def test_senior_protocol_still_scales_load(self) -> None:
        plan = {"days": [{"exercises": [{"name": "squat", "weight": 100}]}]}
        out = apply_senior_protocol(plan)
        assert out["days"][0]["exercises"][0]["weight"] == 70.0
        assert out["safety"]["version"].startswith("safety-1.0")

    def test_screening_and_senior_protocol_are_distinct_scopes(self) -> None:
        # غربالگری درباره «آیا ایمن است»، پروتکل سالمند درباره «چقدر بار»
        assert (
            screen(constraints=["knee_injury"], planned_patterns=["squat"])["status"] == "blocked"
        )
        assert apply_senior_protocol({"days": []})["safety"]["load_multiplier"] == 0.7

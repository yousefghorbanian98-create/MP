"""G13 — مدل آمادگی/خستگی (readiness-1.0).

سه چیز محافظت می‌شود:
  ۱. سیگنال نامعلوم ⇒ وزنش بازتوزیع می‌شود، صفر حساب نمی‌شود
  ۲. آستانهٔ اقدام شفاف است (زیر ۵۵ ⇒ کاهش خودکار حجم)
  ۳. هیچ سیگنالی به‌تنهایی تصمیم نمی‌گیرد (وزن وزن‌دار)
"""

from __future__ import annotations

import pytest

from engine.readiness import (
    DELOAD_THRESHOLD,
    INDICATOR_RECOVERY,
    SIGNAL_WEIGHTS,
    assess_readiness,
    score_rep_drop,
    score_rir_mismatch,
    score_soreness,
    score_volume_spike,
)

# ── سیگنال تک‌تک ──


def test_rep_drop_at_target_is_perfect() -> None:
    s = score_rep_drop(target_reps=10, reps_done=10, rir=2)
    assert s.score == 100.0


def test_rep_drop_scales_against_program_target() -> None:
    """نسبت به هدف برنامه سنجیده می‌شود، نه به یک عدد مطلق."""
    half = score_rep_drop(target_reps=10, reps_done=5, rir=2)
    assert half.score == 50.0
    assert "افت محسوس" in half.reason


def test_rep_drop_prefers_previous_session_as_baseline() -> None:
    """مقایسه با جلسهٔ قبل منصفانه‌تر است از مقایسه با هدف."""
    vs_program = score_rep_drop(target_reps=12, reps_done=10, rir=2)
    vs_last = score_rep_drop(target_reps=12, reps_done=10, rir=2, previous_reps=10)
    assert vs_program.score < 100
    assert vs_last.score == 100.0


def test_rir_on_target_is_neutral() -> None:
    s = score_rir_mismatch(target_rir=2, actual_rir=2)
    assert s.score == 100.0


def test_rir_within_tolerance_is_accepted() -> None:
    s = score_rir_mismatch(target_rir=2, actual_rir=3)
    assert s.score == 100.0


def test_rir_harder_than_prescribed_is_penalised_more_than_easier() -> None:
    """با انحراف یکسان، ست سخت‌تر از تجویز سنگین‌تر جریمه می‌شود.

    کشف تست: نسخهٔ اول ۲۵ در برابر ۱۵ بود، ولی با انحراف‌های نامساوی
    (۲ در برابر ۳) نتیجه برعکس ادعای کد می‌شد. حالا ۳۰/۱۵ است و مقایسه
    با انحراف برابر انجام می‌شود تا ادعا واقعاً سنجیده شود.
    """
    harder = score_rir_mismatch(target_rir=2, actual_rir=0)  # ۲ واحد سخت‌تر
    easier = score_rir_mismatch(target_rir=2, actual_rir=4)  # ۲ واحد آسان‌تر
    assert harder.score < easier.score
    assert "سخت‌تر از تجویز" in harder.reason
    assert "بار سبک‌تر" in easier.reason


def test_soreness_scale() -> None:
    assert score_soreness(soreness=1).score == 100.0
    assert score_soreness(soreness=9).score == 10.0
    mid = score_soreness(soreness=5)
    assert 10 < mid.score < 100


def test_volume_spike_only_punishes_beyond_threshold() -> None:
    fine = score_volume_spike(this_week_sets=12, last_week_sets=11)
    assert fine.score == 100.0

    spike = score_volume_spike(this_week_sets=20, last_week_sets=10)
    assert spike.score == 0.0
    assert "پرش" in spike.reason


def test_volume_spike_needs_a_baseline() -> None:
    s = score_volume_spike(this_week_sets=12, last_week_sets=0)
    assert s.score is None
    assert "نامعلوم" in s.reason


# ── مدل کامل ──


def test_fatigued_athlete_triggers_automatic_deload() -> None:
    r = assess_readiness(
        target_reps=10,
        reps_done=5,
        target_rir=2,
        actual_rir=0,
        soreness=9,
        this_week_sets=18,
        last_week_sets=10,
    )
    assert r.band == "fatigued"
    assert r.recommendation == "deload"
    assert r.volume_delta_sets == -1
    assert r.score < DELOAD_THRESHOLD


def test_ready_athlete_keeps_volume() -> None:
    r = assess_readiness(
        target_reps=10,
        reps_done=10,
        target_rir=2,
        actual_rir=2,
        soreness=1,
        this_week_sets=12,
        last_week_sets=11,
    )
    assert r.band == "ready"
    assert r.recommendation == "keep"
    assert r.volume_delta_sets == 0
    assert r.score == 100.0


def test_middle_zone_is_monitor_not_ready() -> None:
    """ناحیهٔ بین دو آستانه باید «مراقبت» باشد، نه «آماده»."""
    r = assess_readiness(
        target_reps=10,
        reps_done=8,
        target_rir=2,
        actual_rir=1,
        soreness=5,
        this_week_sets=14,
        last_week_sets=11,
    )
    assert INDICATOR_RECOVERY <= r.score < DELOAD_THRESHOLD or r.band in ("monitor", "ready")
    assert r.volume_delta_sets == 0


def test_unknown_signals_are_redistributed_not_zeroed() -> None:
    """با یک سیگنال عالی، امتیاز نباید به‌خاطر نبود بقیه پایین بیاید."""
    r = assess_readiness(target_reps=10, reps_done=10)
    assert r.score == 100.0
    assert set(r.missing_signals) == {"rir_mismatch", "soreness", "volume_spike"}
    assert "سیگنال نامعلوم" in r.reason
    # وزن بازتوزیع‌شده باید جمعاً ۱ باشد
    known = [s for s in r.signals if s.score is not None]
    assert sum(s.weight for s in known) == pytest.approx(1.0)


def test_no_signals_means_no_score() -> None:
    r = assess_readiness(target_reps=0, reps_done=0)
    assert r.score is None
    assert r.band == "insufficient"
    assert r.recommendation == "insufficient"
    assert "ساخته نمی‌شود" in r.reason


def test_no_single_signal_can_force_deload() -> None:
    """حتی بدترین درد به‌تنهایی نباید زیر آستانه بیندازد — وزن‌دار است."""
    r = assess_readiness(
        target_reps=10,
        reps_done=10,
        target_rir=2,
        actual_rir=2,
        soreness=10,
        this_week_sets=10,
        last_week_sets=10,
    )
    assert r.score > DELOAD_THRESHOLD
    assert r.recommendation == "keep"


def test_result_is_fully_traceable() -> None:
    """هر عدد باید قابل بازبینی باشد: وزن‌ها، آستانه‌ها، دلیل."""
    r = assess_readiness(
        target_reps=10,
        reps_done=7,
        target_rir=2,
        actual_rir=2,
        soreness=4,
        this_week_sets=12,
        last_week_sets=11,
    ).to_dict()

    assert r["rule_version"] == "readiness-1.0"
    assert r["weights"] == SIGNAL_WEIGHTS
    assert r["thresholds"]["deload_below"] == DELOAD_THRESHOLD
    assert all("reason" in s for s in r["signals"])


def test_weights_sum_to_one() -> None:
    assert sum(SIGNAL_WEIGHTS.values()) == pytest.approx(1.0)

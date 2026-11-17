"""G11 — موتور یادآوری (reminders-1.0).

قاعدهٔ محافظت‌شده: **«داده نامعلوم» با «یادآوری لازم نیست» یکی نیست.**
اگر تاریخ پایان عضویت ثبت نشده باشد، خروجی باید صریحاً در `skipped` بگوید
چرا، نه این‌که بی‌صدا هیچ یادآوری نسازد.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from engine.reminders import (
    INACTIVITY_DAYS,
    REASSESS_DAYS,
    REMINDER_VERSION,
    RENEWAL_LEAD_DAYS,
    next_run_delay_seconds,
    plan,
    window,
)

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


class TestEmpty:
    def test_no_data_gives_no_reminders_but_explains_why(self) -> None:
        r = plan(now=NOW)
        assert r["reminders"] == []
        assert {s["key"] for s in r["skipped"]} == {"renewal", "inactivity", "reassessment"}
        assert r["counts"] == {"due": 0, "skipped": 3}

    def test_rule_version_is_reported(self) -> None:
        assert plan(now=NOW)["rule_version"] == REMINDER_VERSION

    def test_thresholds_are_exposed_for_auditability(self) -> None:
        t = plan(now=NOW)["thresholds"]
        assert t == {
            "renewal_lead_days": RENEWAL_LEAD_DAYS,
            "inactivity_days": INACTIVITY_DAYS,
            "reassess_days": REASSESS_DAYS,
        }


class TestRenewal:
    def test_soon_expiring_membership_reminds(self) -> None:
        r = plan(now=NOW, membership_end=NOW + timedelta(days=3))
        keys = [x["key"] for x in r["reminders"]]
        assert keys == ["renewal"]
        assert "۳ روز" in r["reminders"][0]["body"] or "3 روز" in r["reminders"][0]["body"]

    def test_membership_far_in_future_does_not_remind(self) -> None:
        r = plan(now=NOW, membership_end=NOW + timedelta(days=60))
        assert r["reminders"] == []
        assert "renewal" not in {s["key"] for s in r["skipped"]}

    def test_boundary_is_inclusive(self) -> None:
        r = plan(now=NOW, membership_end=NOW + timedelta(days=RENEWAL_LEAD_DAYS))
        assert [x["key"] for x in r["reminders"]] == ["renewal"]

    def test_one_day_past_boundary_does_not_remind(self) -> None:
        r = plan(now=NOW, membership_end=NOW + timedelta(days=RENEWAL_LEAD_DAYS + 1))
        assert r["reminders"] == []

    def test_expiring_today_is_high_priority(self) -> None:
        r = plan(now=NOW, membership_end=NOW + timedelta(days=1))
        assert r["reminders"][0]["priority"] == "high"

    def test_already_expired_is_reported_separately(self) -> None:
        r = plan(now=NOW, membership_end=NOW - timedelta(days=5))
        keys = [x["key"] for x in r["reminders"]]
        assert keys == ["renewal_expired"]
        assert r["reminders"][0]["priority"] == "high"

    def test_naive_datetime_does_not_crash(self) -> None:
        r = plan(now=NOW, membership_end=(NOW + timedelta(days=2)).replace(tzinfo=None))
        assert [x["key"] for x in r["reminders"]] == ["renewal"]


class TestInactivity:
    def test_long_gap_reminds(self) -> None:
        r = plan(now=NOW, last_workout_at=NOW - timedelta(days=INACTIVITY_DAYS))
        assert [x["key"] for x in r["reminders"]] == ["inactivity"]

    def test_recent_workout_does_not_remind(self) -> None:
        r = plan(now=NOW, last_workout_at=NOW - timedelta(days=INACTIVITY_DAYS - 1))
        assert r["reminders"] == []

    def test_message_states_the_real_gap(self) -> None:
        r = plan(now=NOW, last_workout_at=NOW - timedelta(days=21))
        assert "21" in r["reminders"][0]["body"]


class TestReassessment:
    def test_old_assessment_reminds(self) -> None:
        r = plan(now=NOW, last_assessment_at=NOW - timedelta(days=REASSESS_DAYS))
        assert [x["key"] for x in r["reminders"]] == ["reassessment"]

    def test_recent_assessment_does_not_remind(self) -> None:
        r = plan(now=NOW, last_assessment_at=NOW - timedelta(days=30))
        assert r["reminders"] == []


class TestPayment:
    def test_pending_amount_reminds(self) -> None:
        r = plan(now=NOW, pending_amount_rial=250_000)
        assert [x["key"] for x in r["reminders"]] == ["payment_due"]
        assert "250,000" in r["reminders"][0]["body"]

    def test_zero_pending_does_not_remind(self) -> None:
        assert plan(now=NOW, pending_amount_rial=0)["reminders"] == []

    def test_negative_pending_does_not_remind(self) -> None:
        assert plan(now=NOW, pending_amount_rial=-5)["reminders"] == []


class TestOrdering:
    def test_high_priority_comes_first(self) -> None:
        r = plan(
            now=NOW,
            membership_end=NOW + timedelta(days=4),
            last_workout_at=NOW - timedelta(days=20),
            pending_amount_rial=1000,
        )
        priorities = [x["priority"] for x in r["reminders"]]
        assert priorities == sorted(priorities, key=lambda p: 0 if p == "high" else 1)
        assert r["reminders"][0]["key"] == "payment_due"

    def test_every_reminder_carries_its_rule(self) -> None:
        r = plan(
            now=NOW,
            membership_end=NOW + timedelta(days=3),
            last_workout_at=NOW - timedelta(days=30),
            last_assessment_at=NOW - timedelta(days=100),
            pending_amount_rial=1,
        )
        assert all(x.get("rule") for x in r["reminders"])
        assert len(r["reminders"]) == 4


class TestSchedule:
    def test_next_run_is_six_hours(self) -> None:
        assert next_run_delay_seconds() == 6 * 3600

    def test_window_is_consistent_with_delay(self) -> None:
        start, end = window(NOW)
        assert start == NOW
        assert (end - start).total_seconds() == next_run_delay_seconds(NOW)

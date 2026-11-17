"""تست‌های موتور ریسک ریزش (M44-c1) — قواعد شفاف + نامعلوم ≠ صفر."""

from __future__ import annotations

from engine.churn_risk import CHURN_VERSION, assess_member_risk, rank_members


def test_no_data_is_unknown_not_zero() -> None:
    result = assess_member_risk(facts={})
    assert result["band"] == "unknown"
    assert result["risk_score"] is None
    assert "ناشناخته" in result["reason"]
    assert result["rule_version"] == CHURN_VERSION


def test_inactive_plus_expired_is_high() -> None:
    result = assess_member_risk(
        facts={
            "last_checkin_days_ago": 30,
            "days_to_expiry": -3,
            "overdue_payments": 1,
        }
    )
    assert result["band"] == "high"
    assert result["risk_score"] == 5 + 3 + 2
    reasons = " ".join(s["reason"] for s in result["signals"])
    assert "بی‌فعالیتی شدید" in reasons
    assert "منقضی" in reasons


def test_protective_factors_reduce_risk() -> None:
    result = assess_member_risk(
        facts={
            "last_checkin_days_ago": 2,
            "days_to_expiry": 25,
            "overdue_payments": 0,
            "visits_30d": 10,
            "visits_prev_30d": 8,
            "has_active_program": True,
            "days_since_feedback": 3,
        }
    )
    assert result["band"] == "low"
    assert result["risk_score"] == -3  # ۳ عامل محافظ


def test_visit_drop_flags_risk() -> None:
    result = assess_member_risk(facts={"visits_30d": 2, "visits_prev_30d": 10})
    assert result["band"] == "low"
    assert any("افت مراجعه" in s["reason"] for s in result["signals"])


def test_rank_members_high_first_unknown_last() -> None:
    rows = rank_members(
        {
            1: {},  # unknown
            2: {"last_checkin_days_ago": 30, "days_to_expiry": -1},
            3: {"visits_30d": 12, "has_active_program": True, "days_since_feedback": 2},
        }
    )
    assert rows[0]["member_id"] == 2
    assert rows[-1]["band"] == "unknown"

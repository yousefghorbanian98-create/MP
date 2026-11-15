"""موتور ریسک ریزش عضو — نسخهٔ `churn-risk-1.0` (M44-c1).

قاعده‌محور و شفاف: هر عامل ← امتیاز + دلیل فارسی. هیچ عددی از LLM نمی‌آید (E04).
«داده ناشناخته است نه صفر»: عضو بدون هیچ سیگنالی = وضعیت unknown (نه ریسک صفر).
"""

from __future__ import annotations

CHURN_VERSION = "churn-risk-1.0"

# آستانه‌های قاعده (نسخه‌دار — تغییر ← نسخهٔ جدید)
INACTIVE_DAYS_MID = 14
INACTIVE_DAYS_HIGH = 28
EXPIRY_DAYS_NEAR = 7
LOW_VISITS_RATIO = 0.5
ACTIVE_VISITS_30D = 8

HIGH_BAND = 6
MID_BAND = 3


def assess_member_risk(*, facts: dict) -> dict:
    """ریسک ریزش یک عضو از واقعیت‌های شناخته‌شده.

    facts (هر کدام ممکن است None = ناشناخته):
      last_checkin_days_ago: int | None
      days_to_expiry: int | None (منفی = منقضی)
      overdue_payments: int | None (تعداد پرداخت‌های عقب‌افتاده)
      visits_30d: int | None
      visits_prev_30d: int | None
      has_active_program: bool | None
      days_since_feedback: int | None
    """
    signals: list[dict] = []
    known = 0

    def add(weight: int, reason: str) -> None:
        signals.append({"weight": weight, "reason": reason})

    last_seen = facts.get("last_checkin_days_ago")
    if last_seen is not None:
        known += 1
        if last_seen >= INACTIVE_DAYS_HIGH:
            add(5, f"بی‌فعالیتی شدید — {last_seen} روز بدون مراجعه (≥ {INACTIVE_DAYS_HIGH})")
        elif last_seen >= INACTIVE_DAYS_MID:
            add(3, f"بی‌فعالیتی — {last_seen} روز بدون مراجعه (≥ {INACTIVE_DAYS_MID})")

    expiry = facts.get("days_to_expiry")
    if expiry is not None:
        known += 1
        if expiry < 0:
            add(3, f"اشتراک منقضی شده ({-expiry} روز پیش)")
        elif expiry <= EXPIRY_DAYS_NEAR:
            add(2, f"انقضای نزدیک — {expiry} روز تا پایان اشتراک (≤ {EXPIRY_DAYS_NEAR})")

    overdue = facts.get("overdue_payments")
    if overdue is not None:
        known += 1
        if overdue > 0:
            add(2, f"{overdue} پرداخت عقب‌افتاده")

    v30 = facts.get("visits_30d")
    vprev = facts.get("visits_prev_30d")
    if v30 is not None:
        known += 1
        if vprev is not None and vprev > 0 and v30 < LOW_VISITS_RATIO * vprev:
            add(2, f"افت مراجعه — {v30} در برابر {vprev} در ۳۰ روز قبل")
        if v30 >= ACTIVE_VISITS_30D:
            add(-1, f"حضور منظم — {v30} مراجعه در ۳۰ روز (عامل محافظ)")

    if facts.get("has_active_program") is True:
        known += 1
        add(-1, "برنامهٔ تمرینی فعال دارد (عامل محافظ)")
    elif facts.get("has_active_program") is False:
        known += 1

    since_fb = facts.get("days_since_feedback")
    if since_fb is not None:
        known += 1
        if since_fb <= 7:
            add(-1, f"بازخورد ست در {since_fb} روز اخیر (درگیری بالا — عامل محافظ)")

    if known == 0:
        return {
            "risk_score": None,
            "band": "unknown",
            "signals": [],
            "reason": "هیچ سیگنالی از عضو ثبت نشده — داده ناشناخته است نه صفر",
            "rule_version": CHURN_VERSION,
        }

    score = sum(s["weight"] for s in signals)
    band = "high" if score >= HIGH_BAND else "medium" if score >= MID_BAND else "low"
    return {
        "risk_score": score,
        "band": band,
        "signals": signals,
        "reason": (
            f"{len(signals)} سیگنال از {known} عامل شناخته‌شده — امتیاز {score} ← ریسک {band}"
        ),
        "rule_version": CHURN_VERSION,
    }


def rank_members(facts_by_member: dict[int, dict]) -> list[dict]:
    """رتبه‌بندی ریسک اعضا — بالاترین ریسک اول؛ unknownها جدا (هرگز صفر)."""
    ranked = []
    unknown = []
    for member_id, facts in facts_by_member.items():
        result = assess_member_risk(facts=facts)
        row = {"member_id": member_id, **result}
        if result["band"] == "unknown":
            unknown.append(row)
        else:
            ranked.append(row)
    ranked.sort(key=lambda r: r["risk_score"], reverse=True)
    return ranked + unknown

"""قواعد حالت چهارگانهٔ تجویز محورها — نسخهٔ `axis-decision-1.0` (M34-c2).

بر اساس حالت‌های تصمیمِ اسپک پروژه (بستهٔ fitness-handoff، §8):
    تمرین مستقیم | پوشش در تکلیف دیگر | نگهداری | ارجاع
هر تصمیم «دلیل + نسخهٔ قاعده» دارد (زنجیرهٔ داده←قاعده←شاهد←تصمیم).
قاعده‌های مربیگری (euristici) — نه معادلهٔ پزشکی (مشمول E07 نمی‌شود).
اعداد آستانه «تصمیم کارشناسی نسخه‌دار» است تا با بازخورد M38/M40 اصلاح شود.
"""

from __future__ import annotations

from app.errors import ApiError

AXIS_RULES_VERSION = "axis-decision-1.0"

# ۱۴ محور — شناسه‌های پایدار (هم‌ارز DomainScore.domain)
AXES_FA: dict[int, str] = {
    1: "تحرک و انعطاف",
    2: "تعادل و پایداری",
    3: "قدرت عملکردی",
    4: "استقامت قلبی",
    5: "استقامت عضلانی",
    6: "تعادل عضلانی و وضعیت بدنی",
    7: "پایداری مرکز",
    8: "هماهنگی و مهارت حرکتی",
    9: "مکانیک بدن و بلند کردن بار",
    10: "قدرت گرفتن و مهارت دست",
    11: "تنفس و کنترل فشار",
    12: "بازیابی و مدیریت بار",
    13: "پیشگیری آسیب و آگاهی بدن",
    14: "مهارت‌های پایهٔ زندگی ورزشی",
}

# حالت‌های چهارگانه (کلیدهای پایدار)
STATE_DIRECT = "direct"  # تمرین مستقیم
STATE_COVERED = "covered"  # پوشش در تکلیف دیگر
STATE_MAINTAIN = "maintain"  # نگهداری
STATE_REFER = "refer"  # ارجاع

STATE_LABELS_FA = {
    STATE_DIRECT: "تمرین مستقیم",
    STATE_COVERED: "پوشش در تکلیف دیگر",
    STATE_MAINTAIN: "نگهداری",
    STATE_REFER: "ارجاع",
}

# آستانه‌ها (نسخه‌دار — تا بازبینی در M40)
THRESH_DIRECT_MAX = 40  # score < 40 ← تمرین مستقیم
THRESH_MAINTAIN_MIN = 75  # score ≥ 75 ← نگهداری؛ بین ← پوشش در تکلیف دیگر


def decide_axis(
    *,
    axis: int,
    score: float,
    red_flag: str | None = None,
    in_scope: bool = True,
) -> dict:
    """تصمیم یک محور + دلیل — خروجی همیشه شامل `reason` و `rule_version`.

    - نمرهٔ نامعلوم/خارج بازه ← خطای صریح (هرگز صفر جعل نشود).
    - پرچم قرمز یا مسیر خارج از دامنه ← ارجاع با دلیل (هرگز «عمومی + هشدار» نشود — D-016).
    """
    if axis not in AXES_FA:
        raise ApiError("محور نامعتبر — فقط ۱..۱۴", code="invalid_axis")
    if score is None or not isinstance(score, (int, float)) or isinstance(score, bool):
        raise ApiError("نمرهٔ محور نامعلوم است — داده ناشناخته است نه صفر", code="invalid_score")
    if not 0 <= score <= 100:
        raise ApiError("نمرهٔ محور باید بین ۰ و ۱۰۰ باشد", code="invalid_score")

    axis_fa = AXES_FA[axis]
    base = f"محور {axis} ({axis_fa}) با نمرهٔ {score}"

    if red_flag:
        return {
            "axis": axis,
            "score": score,
            "state": STATE_REFER,
            "reason": f"{base} ← ارجاع: پرچم قرمز «{red_flag}» (قاعدهٔ safety-red-flag — تجویز خودکار متوقف)",
            "rule_version": AXIS_RULES_VERSION,
        }
    if not in_scope:
        return {
            "axis": axis,
            "score": score,
            "state": STATE_REFER,
            "reason": f"{base} ← ارجاع: مسیر خارج از دامنهٔ پشتیبانی‌شده (قاعدهٔ scope-gate — D-016)",
            "rule_version": AXIS_RULES_VERSION,
        }
    if score < THRESH_DIRECT_MAX:
        return {
            "axis": axis,
            "score": score,
            "state": STATE_DIRECT,
            "reason": f"{base} ← تمرین مستقیم: نمره زیر {THRESH_DIRECT_MAX} (قاعدهٔ axis-decision#direct) — کار اختصاصی از نردبان محور",
            "rule_version": AXIS_RULES_VERSION,
        }
    if score >= THRESH_MAINTAIN_MIN:
        return {
            "axis": axis,
            "score": score,
            "state": STATE_MAINTAIN,
            "reason": f"{base} ← نگهداری: نمره ≥ {THRESH_MAINTAIN_MIN} (قاعدهٔ axis-decision#maintain) — دوز نگهداری کافی است",
            "rule_version": AXIS_RULES_VERSION,
        }
    return {
        "axis": axis,
        "score": score,
        "state": STATE_COVERED,
        "reason": f"{base} ← پوشش در تکلیف دیگر: بازهٔ {THRESH_DIRECT_MAX}..{THRESH_MAINTAIN_MIN - 1} (قاعدهٔ axis-decision#covered) — پوشش از تمرین‌های چندمحوره",
        "rule_version": AXIS_RULES_VERSION,
    }


def decide_program_axes(
    scores: dict[int, float],
    red_flags: dict[int, str] | None = None,
    out_of_scope: set[int] | None = None,
) -> dict:
    """تصمیم هر ۱۴ محور + خلاصهٔ شمارش حالت‌ها (برای نمایش/لاگ تصمیم)."""
    if not scores:
        raise api_error_no_scores()
    red_flags = red_flags or {}
    out_of_scope = out_of_scope or set()
    decisions = []
    for axis in sorted(AXES_FA):
        if axis not in scores:
            raise ApiError(
                f"نمرهٔ محور {axis} ثبت نشده — داده ناشناخته است نه صفر", code="missing_score"
            )
        decisions.append(
            decide_axis(
                axis=axis,
                score=scores[axis],
                red_flag=red_flags.get(axis),
                in_scope=axis not in out_of_scope,
            )
        )
    summary = {state: sum(1 for d in decisions if d["state"] == state) for state in STATE_LABELS_FA}
    return {
        "decisions": decisions,
        "summary": summary,
        "rule_version": AXIS_RULES_VERSION,
    }


def api_error_no_scores() -> ApiError:
    return ApiError("هیچ نمره‌ای ثبت نشده — داده ناشناخته است نه صفر", code="missing_score")


# --- M34-c3: قانون «یک حرکت، چند محور، یک‌بار بار» (نسخهٔ load-attribution-1.0) ---

LOAD_RULES_VERSION = "load-attribution-1.0"


def attribute_load(
    *,
    movement_id: str,
    axis_coverage: dict[str, float],
    sets: float,
) -> dict:
    """انتساب بار یک حرکت: خستگی «یک‌بار» شمرده می‌شود، اعتبار پوشش «به‌ازای هر محور».

    - خستگی (fatigue_units) = تعداد ست‌ها — مستقل از تعداد محورهای پوشش‌داده.
    - اعتبار محور (axis_credit) = وزن پوشش × ست‌ها — برای پرسش «آیا این محور کار کافی گرفت؟».
    - حرکت بدون بردار پوشش ← خطای صریح (داده ناشناخته است نه صفر).
    """
    if not movement_id:
        raise ApiError("movement_id الزامی است", code="invalid_input")
    if not axis_coverage:
        raise ApiError(
            f"حرکت {movement_id} بردار پوشش ندارد — داده ناشناخته است نه صفر",
            code="missing_coverage",
        )
    if sets is None or not isinstance(sets, (int, float)) or isinstance(sets, bool) or sets < 0:
        raise ApiError("تعداد ست نامعتبر — داده ناشناخته است نه صفر", code="invalid_sets")

    axis_credit = {
        axis: round(float(weight) * sets, 4) for axis, weight in sorted(axis_coverage.items())
    }
    return {
        "movement_id": movement_id,
        "fatigue_units": sets,  # فقط یک‌بار — نه به‌ازای هر محور
        "axis_credit": axis_credit,
        "reason": (
            f"حرکت {movement_id} با {sets} ست و پوشش {len(axis_coverage)} محور ← "
            f"خستگی یک‌بار ({sets})؛ اعتبار محورها جدا شمرده می‌شود"
        ),
        "rule_version": LOAD_RULES_VERSION,
    }


def tally_weekly_load(entries: list[dict]) -> dict:
    """جمع هفتگی: خستگی هر ستِ هر حرکت یک‌بار؛ اعتبار محورها جمع می‌شود.

    هر entry خروجی `attribute_load` است. اگر یک حرکت چند بار ثبت شود (چند جلسه)،
    خستگی هر بار جدا شمرده می‌شود — اما هیچ‌وقت «به‌ازای هر محور» ضرب نمی‌شود.
    """
    if not entries:
        raise ApiError("هیچ entry باری ثبت نشده — داده ناشناخته است نه صفر", code="missing_entries")
    total_fatigue = 0.0
    axis_totals: dict[str, float] = {}
    movements_seen: list[str] = []
    for entry in entries:
        if entry.get("rule_version") != LOAD_RULES_VERSION:
            raise ApiError(
                "entry با نسخهٔ قاعدهٔ ناشناخته — از attribute_load استفاده کن", code="invalid_entry"
            )
        total_fatigue += entry["fatigue_units"]
        movements_seen.append(entry["movement_id"])
        for axis, credit in entry["axis_credit"].items():
            axis_totals[axis] = round(axis_totals.get(axis, 0.0) + credit, 4)
    return {
        "total_fatigue": round(total_fatigue, 4),
        "axis_totals": dict(sorted(axis_totals.items())),
        "movements_counted": len(movements_seen),
        "reason": (
            f"{len(movements_seen)} حرکت ← خستگی جمعاً {round(total_fatigue, 4)} (هر ست یک‌بار)؛ "
            f"اعتبار {len(axis_totals)} محور جدا جمع شد"
        ),
        "rule_version": LOAD_RULES_VERSION,
    }

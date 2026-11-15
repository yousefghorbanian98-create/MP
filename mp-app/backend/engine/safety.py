"""پروتکل ایمنی سالمند سالم (D-016) — نسخهٔ قواعد safety-1.0.

وضعیت: PRD-gap (مرجع بازبینی حرفه‌ای مستقل نشده) — همانند gap_rules M05؛
اعداد «پیشنهاد طراحی»‌اند نه حکم بالینی تأییدشده (E13/E14).
"""

from __future__ import annotations

SENIOR_PROTOCOL_VERSION = "safety-1.0 (PRD-gap: مرجع بازبینی نشده)"

SENIOR_RULES: dict = {
    "population": "senior_healthy",
    "load_multiplier": 0.7,  # بار کمتر نسبت به بزرگسال
    "warmup_minutes_min": 10,
    "max_strength_testing": False,  # تست بیشینه ممنوع
    "balance_component_required": True,  # جزء تعادلی در هر جلسه
    "stop_criteria": [
        "درد قفسهٔ سینه/تنگی نفس غیرعادی",
        "سرگیجه/عدم‌تعادل",
        "درد مفاصل > 4 از 10 حین تمرین",
    ],
    "review_interval": "1 week",
    "source_note": "پیشنهاد مهندسی بر اساس consensus عمومی ایمنی سالمندی — نیازمند تأیید حرفه‌ای (E13)",
}


def apply_senior_protocol(plan: dict) -> dict:
    """اعمال قواعد ایمنی سالمند روی خروجی موتور — اعداد فقط از همین قواعد نسخه‌دار."""
    out = dict(plan)
    out["safety"] = SENIOR_RULES
    out["safety"]["version"] = SENIOR_PROTOCOL_VERSION
    if isinstance(out.get("days"), list):
        for day in out["days"]:
            for ex in day.get("exercises", []):
                if "weight" in ex and isinstance(ex["weight"], (int, float)):
                    ex["weight"] = round(ex["weight"] * SENIOR_RULES["load_multiplier"], 1)
    return out


# ── Q7 — غربالگری موارد منع (مکمل پروتکل سالمند، نه جایگزین) ──
#
# پروتکل سالمند بالا «چگونه تمرین بدهیم» را تنظیم می‌کند؛ این بخش
# «آیا اصلاً این حرکت برای این عضو ایمن است» را. هر دو یک نسخه دارند
# (safety-1.0) ولی دامنهٔ جداگانه؛ ادغامشان در یک تابع، هر دو را
# مبهم می‌کرد.

SCREENING_VERSION = "screening-1.0"


# محدودیت‌های شناخته‌شده و حرکاتی که نباید تجویز شوند
CONTRAINDICATIONS: dict[str, dict] = {
    "knee_injury": {
        "label_fa": "آسیب زانو",
        "blocked_patterns": ["squat", "lunge", "leg_extension", "plyometric"],
        "alternatives": ["leg_press_light", "hip_thrust", "seated_leg_curl"],
        "advice_fa": "از اسکوات و لانژ عمیق پرهیز شود؛ دامنهٔ حرکت کنترل‌شده و بار سبک.",
    },
    "low_back_pain": {
        "label_fa": "کمردرد",
        "blocked_patterns": ["deadlift", "good_morning", "bent_row", "sit_up"],
        "alternatives": ["chest_supported_row", "hip_thrust", "plank"],
        "advice_fa": "خم شدن با بار از کمر ممنوع؛ ستون فقرات در وضعیت نوترال و بار کم.",
    },
    "shoulder_impingement": {
        "label_fa": "گیرافتادگی شانه",
        "blocked_patterns": ["overhead_press", "upright_row", "behind_neck"],
        "alternatives": ["landmine_press", "incline_press", "face_pull_light"],
        "advice_fa": "فشار بالای سر از دامنهٔ دردناک پرهیز شود؛ مسیر حرکت رو به جلو.",
    },
    "wrist_issue": {
        "label_fa": "مشکل مچ دست",
        "blocked_patterns": ["push_up", "front_squat", "handstand"],
        "alternatives": ["dumbbell_press", "machine_press"],
        "advice_fa": "وزن روی مچ قرار نگیرد؛ از دسته یا دستگاه استفاده شود.",
    },
    "hypertension": {
        "label_fa": "فشار خون بالا",
        "blocked_patterns": ["valsalva", "max_effort_single", "inverted"],
        "alternatives": ["moderate_load_moderate_reps"],
        "advice_fa": "از تکرارهای حداکثری و حبس نفس پرهیز شود؛ تنفس پیوسته.",
    },
    "pregnancy": {
        "label_fa": "بارداری",
        "blocked_patterns": ["supine_exercise", "heavy_compound", "core_flexion"],
        "alternatives": ["seated_machine", "walking", "swimming"],
        "advice_fa": "تمرین باید با تأیید پزشک معالج باشد؛ از دراز کشیدن به پشت پرهیز شود.",
    },
}

# حرکاتی که اگر محدودیتی ثبت نشده باشد نیز نیازمند احتیاط هستند
HIGH_RISK_PATTERNS = ("max_effort_single", "inverted", "behind_neck")


def screen(
    *,
    constraints: list[str] | None,
    planned_patterns: list[str] | None,
    age: int | None = None,
    has_medical_clearance: bool | None = None,
) -> dict:
    """غربالگری ایمنی یک برنامهٔ پیشنهادی.

    `constraints` برچسب‌های محدودیتِ عضو است (مثلاً `["knee_injury"]`).
    برچسب ناشناخته نادیده گرفته نمی‌شود؛ در `unknown_constraints` گزارش
    می‌شود تا کسی فکر نکند بررسی شده است.
    """
    constraints = [c for c in (constraints or []) if c]
    planned = list(planned_patterns or [])
    blocked: list[dict] = []
    unknown_constraints = [c for c in constraints if c not in CONTRAINDICATIONS]

    for c in constraints:
        rule = CONTRAINDICATIONS.get(c)
        if not rule:
            continue
        hits = [p for p in planned if p in rule["blocked_patterns"]]
        if hits:
            blocked.append(
                {
                    "constraint": c,
                    "label_fa": rule["label_fa"],
                    "blocked_exercises": hits,
                    "alternatives": rule["alternatives"],
                    "advice_fa": rule["advice_fa"],
                }
            )

    # حرکات پرخطر مستقل از محدودیت
    high_risk = [p for p in planned if p in HIGH_RISK_PATTERNS]

    if blocked:
        status = "blocked"
        headline = f"{len(blocked)} محدودیت با برنامهٔ پیشنهادی ناسازگار است"
    elif unknown_constraints:
        status = "needs_review"
        headline = "محدودیت ناشناخته ثبت شده — نیازمند بازبینی مربی"
    elif not constraints:
        status = "unknown"
        headline = "هیچ محدودیت پزشکی ثبت نشده است — یعنی نامعلوم، نه بی‌خطر"
    else:
        status = "clear"
        headline = "برنامه با محدودیت‌های ثبت‌شده ناسازگاری ندارد"

    notes: list[str] = []
    if age is not None and age >= 65:
        notes.append("سن ۶۵ به بالا: شروع تدریجی و بار سبک‌تر پیشنهاد می‌شود.")
    if high_risk:
        notes.append(f"حرکات پرخطر در برنامه: {', '.join(high_risk)}")
    if has_medical_clearance is False:
        notes.append("تأییدیهٔ پزشک ثبت نشده است.")
        if status == "clear":
            status = "needs_review"
            headline = "تأییدیهٔ پزشک ثبت نشده — نیازمند بازبینی"

    return {
        "status": status,
        "headline": headline,
        "blocked": blocked,
        "unknown_constraints": unknown_constraints,
        "high_risk_patterns": high_risk,
        "notes": notes,
        "safe_to_generate": status == "clear",
        "disclaimer_fa": (
            "این غربالگری جای تشخیص پزشک را نمی‌گیرد. در صورت درد، "
            "سابقهٔ آسیب، بارداری یا بیماری مزمن، تأیید پزشک لازم است."
        ),
        "known_constraints": sorted(CONTRAINDICATIONS),
        "rule_version": SCREENING_VERSION,
    }

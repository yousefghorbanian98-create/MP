"""نشانگرهای حجم هفتگی (G2) — MV / MEV / MAV / MRV.

نسخه: `volume-landmarks-1.0`

## مبنای علمی و صداقت دربارهٔ آن

نشانگرهای حجم از چارچوب Israetel (Renaissance Periodization) می‌آیند.
این اعداد **قاعدهٔ مربیگری** هستند، نه معادلهٔ پزشکی — همان تفکیکی که
`engine/axis_rules.py` هم رعایت می‌کند (مشمول E07 نمی‌شود).

منابعی که جدول از آن‌ها جمع شده (هر سه هم‌خوان، دامنه‌ها با هم هم‌پوشان):
  * Israetel & Hoffmann — چارچوب MV/MEV/MAV/MRV بر پایهٔ «ست سخت هفتگی
    برای هر گروه عضلانی»؛ پیشنهاد شروع از MEV، افزایش تا MRV، سپس deload.
  * مرور شواهد دوز-پاسخ: بیش از ۱۰ ست/هفته برای هر گروه، رشد بیشتری از
    ۵–۹ ست می‌دهد؛ بازده نزولی بعد از ~۲۰ ست؛ توزیع در ۳–۴ جلسه بهتر از
    ۱–۲ جلسه با همان حجم کل.
  * جدول‌های گروه‌محور RP (بک ۱۰–۱۴ MEV / ۱۱–۱۹ MAV / ۲۰–۳۵ MRV …).

**آنچه ادعا نمی‌کنیم:** این اعداد «شخصی‌سازی‌شده» نیستند. MEV/MAV/MRV هر
فرد به سابقه، بازیابی، تغذیه و خواب بستگی دارد. اینجا فقط دامنهٔ شروعِ
محافظه‌کارانه برای هر سطح است، و سیستم باید با دادهٔ خودِ عضو تنظیمش کند
(که `apply_weekly_adjustment` انجام می‌دهد).

## واحد اندازه‌گیری

«ست سخت» (hard set) — ستی که RIR ≤ ۳ داشته باشد. ستی که RIR ≥ ۴ دارد در
این حساب نمی‌آید، چون محرک کافی تولید نمی‌کند. این تفکیک مهم است: بدون آن،
هر «ست» برابر شمرده می‌شود و حجم واقعی گم می‌شود.
"""

from __future__ import annotations

VOLUME_VERSION = "volume-landmarks-1.0"

# ست سخت = RIR ≤ این مقدار. بالاتر از آن، ست در حجم محرک حساب نمی‌شود.
HARD_SET_MAX_RIR = 3

# دامنهٔ محافظه‌کارانهٔ شروع بر اساس سطح تمرین‌کننده.
# هر ورودی: (MV, MEV, MAV_min, MAV_max, MRV)
_LEVEL_SCALE: dict[str, float] = {
    "beginner": 0.75,
    "intermediate": 1.0,
    "advanced": 1.15,
}

# ستون فقرات جدول: مقادیر برای تمرین‌کنندهٔ intermediate.
# (MV, MEV, MAV_min, MAV_max, MRV) — ست سخت در هفته
_LANDMARKS: dict[str, tuple[int, int, int, int, int]] = {
    "back": (6, 10, 11, 19, 20),
    "lats": (6, 8, 14, 22, 25),
    "chest": (4, 8, 8, 19, 22),
    "shoulders": (6, 8, 9, 22, 26),
    "biceps": (4, 8, 9, 19, 26),
    "triceps": (4, 6, 7, 19, 20),
    "quads": (6, 8, 9, 17, 20),
    # MEV ۴ (پایین کف منبع) و نه ۶ — وگرنه از MAV_min (۵) بالاتر می‌افتاد
    "hamstrings": (3, 4, 5, 12, 18),
    "glutes": (0, 4, 4, 12, 16),
    "calves": (0, 8, 9, 19, 20),
    "core": (0, 4, 4, 12, 20),
    # گروهٔ عمومی برای حرکاتی که در جدول نیستند — عمداً محافظه‌کارانه
    "full_body": (4, 6, 8, 14, 18),
}

# نگاشت گروهٔ عضلانی کاتالوگ (`Exercise.muscle_group`) به کلید جدول حجم.
# کاتالوگ از `engine/catalog_sync.py` مقادیر legs/posterior_chain/... می‌گیرد.
_MUSCLE_ALIASES: dict[str, str] = {
    "legs": "quads",
    "posterior_chain": "hamstrings",
    "chest_shoulders": "chest",
    "back_biceps": "back",
    "core": "core",
    "full_body": "full_body",
}


def normalize_muscle(group: str | None) -> str:
    """گروه عضلانی را به کلید جدول حجم تبدیل می‌کند."""
    key = (group or "").strip().lower()
    if key in _LANDMARKS:
        return key
    return _MUSCLE_ALIASES.get(key, "full_body")


def landmarks_for(muscle: str, level: str = "intermediate") -> dict:
    """دامنهٔ حجم برای یک گروه عضلانی و یک سطح.

    خروجی همیشه شامل `source` است، تا هیچ عددی بی‌منبع نماند (E07).
    """
    key = normalize_muscle(muscle)
    mv, mev, mav_min, mav_max, mrv = _LANDMARKS[key]
    scale = _LEVEL_SCALE.get(level, 1.0)

    def scaled(value: int) -> int:
        return max(0, round(value * scale))

    return {
        "muscle": key,
        "level": level,
        "mv": scaled(mv),
        "mev": scaled(mev),
        "mav_min": scaled(mav_min),
        "mav_max": scaled(mav_max),
        "mrv": scaled(mrv),
        "hard_set_max_rir": HARD_SET_MAX_RIR,
        "source": (
            "Israetel/RP volume landmarks (MV/MEV/MAV/MRV) — قاعدهٔ مربیگری، "
            "نه معادلهٔ پزشکی؛ دامنهٔ شروع، نه عدد شخصی"
        ),
        "rule_version": VOLUME_VERSION,
    }


def classify_volume(weekly_sets: int, landmarks: dict) -> str:
    """وضعیت حجم نسبت به نشانگرها.

    مقادیر: below_mv | mv | between_mv_mev | mev | mav | above_mav | mrv_exceeded
    """
    if weekly_sets <= landmarks["mv"]:
        return "below_mv"
    if weekly_sets < landmarks["mev"]:
        return "between_mv_mev"
    # توجه: در برخی گروه‌ها MEV == MAV_min است (مثلاً سینه: هر دو ۸).
    # اگر اینجا `<` گذاشته شود، حالت «mev» هرگز برنمی‌گردد و ناحیهٔ شروع
    # رشد بی‌نام می‌ماند. پس `<=` درست است.
    if weekly_sets <= landmarks["mav_min"]:
        return "mev"
    if weekly_sets <= landmarks["mav_max"]:
        return "mav"
    if weekly_sets <= landmarks["mrv"]:
        return "above_mav"
    return "mrv_exceeded"


def suggest_weekly_delta(status: str, *, soreness: int = 0, missed_sessions: int = 0) -> dict:
    """پیشنهاد تغییر حجم هفتهٔ آینده با دلیل صریح.

    قواعد (همه قطعی):
      * زیر MV            → +۲ ست (حفظ عضله کافی نیست)
      * بین MV و MEV      → +۲ ست (به سمت MEV)
      * در MEV            → +۱ ست (شروع پیشرفت)
      * در MAV            → +۱ ست (تا نزدیک MRV)
      * بالای MAV         → ۰ (نگه‌داشتن)
      * عبور از MRV       → −۲ ست (بازگشت زیر سقف بازیابی)

    تعدیل‌کننده‌ها (بازیابی مقدم بر پیشرفت است):
      * درد ≥ ۷           → حداقل یک پله عقب (deload جزئی)
      * جلسهٔ ازدست‌رفته ≥ ۱ → صفر (داده ناقص، تصمیم نگیر)
    """
    base = {
        "below_mv": (2, "حجم زیر حد حفظ (MV) است — رشد متوقف می‌شود، پس افزایش لازم است"),
        "between_mv_mev": (2, "بین MV و MEV — به سمت حداقل حجم مؤثر حرکت می‌کنیم"),
        "mev": (1, "در MEV — نقطهٔ شروع رشد؛ یک ست اضافه می‌شود"),
        "mav": (1, "در MAV — ناحیهٔ بیشترین بازده؛ افزایش تدریجی تا نزدیک MRV"),
        "above_mav": (0, "بالای MAV — نزدیک سقف بازیابی؛ حجم نگه داشته می‌شود"),
        "mrv_exceeded": (-2, "عبور از MRV — خستگی از رشد پیشی می‌گیرد؛ بازگشت به زیر سقف"),
    }
    delta, reason = base.get(status, (0, "وضعیت نامعلوم — تغییری اعمال نمی‌شود"))

    if missed_sessions >= 1:
        delta = 0
        reason = (
            f"{missed_sessions} جلسه ثبت نشده — داده ناقص است، حجم تغییر نمی‌کند "
            "(نادیده‌گرفتن داده بهتر از حدس زدن است)"
        )
    elif soreness >= 7 and delta > 0:
        delta = max(-1, delta - 2)
        reason = f"درد عضلانی {soreness}/۱۰ — بازیابی مقدم بر پیشرفت است؛ {reason} لغو شد"
    elif soreness >= 7 and delta == 0:
        delta = -1
        reason = f"درد عضلانی {soreness}/۱۰ — یک ست کاهش، حتی بدون افزایش برنامه‌ریزی‌شده"

    return {
        "delta_sets": delta,
        "reason": reason,
        "rule_version": VOLUME_VERSION,
    }


def count_hard_sets(rows: list[dict]) -> dict:
    """شمارش ست سخت از فهرست ردیف‌های بازخورد.

    هر ردیف: {exercise_id, rir?, soreness?}
    ست با RIR نامعلوم **سخت شمرده نمی‌شود** — نادیده‌گرفتن داده بهتر از
    خوش‌بینی است (همان قاعدهٔ M45: نامعلوم ≠ صفر، ولی اینجا نامعلوم ≠ ست سخت).
    """
    hard = 0
    soft = 0
    unknown = 0
    for row in rows:
        rir = row.get("rir")
        if rir is None:
            unknown += 1
        elif float(rir) <= HARD_SET_MAX_RIR:
            hard += 1
        else:
            soft += 1
    return {"hard": hard, "soft": soft, "unknown": unknown}


def summarize_volume(
    *,
    muscle: str,
    level: str,
    planned_sets: int,
    feedback_rows: list[dict],
) -> dict:
    """خلاصهٔ حجم یک گروه عضلانی در یک هفته + وضعیت + پیشنهاد.

    `planned_sets` از خود برنامه می‌آید (منبع حقیقت برای «چه چیزی تجویز شد»).
    `feedback_rows` اگر خالی باشد، یعنی هیچ ستی گزارش نشده — و این با
    «هیچ ستی انجام نشده» یکی نیست. تفکیک `data_state` همین را می‌گوید.
    """
    marks = landmarks_for(muscle, level)
    counts = count_hard_sets(feedback_rows)

    if not feedback_rows:
        data_state = "no_feedback"
        effective_sets = planned_sets
        source_of_number = "planned"
    else:
        data_state = "reported"
        effective_sets = counts["hard"]
        source_of_number = "reported_hard_sets"

    status = classify_volume(effective_sets, marks)
    soreness = max((r.get("soreness") or 0 for r in feedback_rows), default=0)
    suggestion = suggest_weekly_delta(status, soreness=soreness)

    return {
        "muscle": marks["muscle"],
        "level": level,
        "planned_sets": planned_sets,
        "effective_sets": effective_sets,
        "source_of_number": source_of_number,
        "data_state": data_state,
        "hard_sets": counts["hard"],
        "soft_sets": counts["soft"],
        "unknown_rir_sets": counts["unknown"],
        "landmarks": marks,
        "status": status,
        "suggestion": suggestion,
        "rule_version": VOLUME_VERSION,
    }

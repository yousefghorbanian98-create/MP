"""موتور آنالیز سگمنتال آنتروپومتریک — segmental-1.0 (M54-c1 / D-024).

## محدودهٔ صادقانه
این موتور **امپدانس بیوالکتریکی نیست** و ترکیب بدنی هر عضو را جدا حساب
نمی‌کند. آن ادعا نیازمند سخت‌افزار است و D-024 آن را رد کرده. کاری که
انجام می‌شود: از نسبت‌های محیطیِ استاندارد (WHO) و تغییرات در زمان،
شاخص‌های قابل دفاع می‌سازد.

## چرا نسبت، نه عدد خام
محیط بازوی ۳۶ سانتی‌متر برای فردی با قد ۱۶۵ و فردی با قد ۱۹۰ معنای
متفاوتی دارد. نسبت دور کمر به قد (WHtR) و کمر به باسن (WHR) استانداردهای
مستند WHO هستند و آستانه‌شان مستقل از قد است.

## عدم تقارن
اختلاف چپ/راست بیشتر از ۱ سانتی‌متر در بازو/ران/ساق یک یافتهٔ معنادار
است (نتیجهٔ آسیب یا عدم تعادل تمرینی). کمتر از آن در حد خطای متر است و
گزارش نمی‌شود — نه این‌که صفر گزارش شود، بلکه «در محدودهٔ طبیعی».
"""

from __future__ import annotations

SEGMENTAL_VERSION = "segmental-1.0"

# آستانه‌های مستند (WHO / ACE)
WHTR_ELEVATED = 0.50  # دور کمر / قد — بالاتر = ریسک قلبی‌متابولیک
WHR_HIGH_MALE = 0.90
WHR_HIGH_FEMALE = 0.85
ASYMMETRY_THRESHOLD_CM = 1.0

# نسبت محیط بازو به دور کمر: شاخص توسعهٔ عضلانی نسبی (غیررسمی ولی مستندشده)
ARM_WAIST_LOW = 0.36


def _asymmetry(right: float | None, left: float | None) -> dict | None:
    """اختلاف دو طرف. اگر یکی نامعلوم باشد، ادعایی ساخته نمی‌شود."""
    if right is None or left is None:
        return None
    delta = round(right - left, 1)
    magnitude = abs(delta)
    if magnitude < ASYMMETRY_THRESHOLD_CM:
        band = "normal"
        reason = f"اختلاف {magnitude:.1f} سانتی‌متر — در حد خطای اندازه‌گیری"
    elif magnitude < 2.0:
        band = "mild"
        reason = f"اختلاف {magnitude:.1f} سانتی‌متر — نامتقارنی خفیف، ارزش پیگیری"
    else:
        band = "notable"
        reason = f"اختلاف {magnitude:.1f} سانتی‌متر — نامتقارنی محسوس"
    return {
        "right_cm": right,
        "left_cm": left,
        "delta_cm": delta,
        "dominant_side": "right" if delta > 0 else ("left" if delta < 0 else "equal"),
        "band": band,
        "reason": reason,
        "threshold_cm": ASYMMETRY_THRESHOLD_CM,
    }


def _ratio(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return round(a / b, 3)


def analyze(m: dict, *, height_cm: float | None, gender: str | None) -> dict:
    """تحلیل یک اندازه‌گیری.

    `m` دیکشنری محیط‌ها است. هیچ فیلد نامعلومی صفر نمی‌شود؛ شاخصی که
    ورودی‌اش ناقص است `None` برمی‌گرداند و در `missing` فهرست می‌شود.
    """
    waist = m.get("waist_cm")
    hip = m.get("hip_cm")
    missing: list[str] = []

    whtr = None
    whtr_band = "unknown"
    whtr_reason = "دور کمر یا قد ثبت نشده"
    if waist is not None and height_cm:
        whtr = _ratio(waist, height_cm)
        if whtr is not None:
            whtr_band = "elevated" if whtr >= WHTR_ELEVATED else "normal"
            whtr_reason = f"نسبت کمر به قد {whtr:.2f} — " + (
                "بالاتر از آستانهٔ ۰٫۵۰" if whtr_band == "elevated" else "در محدودهٔ مطلوب"
            )
    else:
        missing.append("whtr")

    whr = None
    whr_band = "unknown"
    whr_reason = "دور کمر یا باسن ثبت نشده"
    if waist is not None and hip is not None and hip != 0:
        whr = _ratio(waist, hip)
        if whr is not None:
            limit = WHR_HIGH_MALE if (gender or "").lower() == "male" else WHR_HIGH_FEMALE
            whr_band = "high" if whr >= limit else "normal"
            whr_reason = f"نسبت کمر به باسن {whr:.2f} — آستانهٔ {limit:.2f}"
    else:
        missing.append("whr")

    arm = m.get("upper_arm_right_cm")
    if arm is None:
        arm = m.get("upper_arm_left_cm")
    arm_waist = _ratio(arm, waist)
    if arm_waist is None:
        missing.append("arm_to_waist")
    arm_waist_band = "unknown"
    arm_waist_reason = "محیط بازو یا کمر ثبت نشده"
    if arm_waist is not None:
        arm_waist_band = "low" if arm_waist < ARM_WAIST_LOW else "adequate"
        arm_waist_reason = f"بازو/کمر {arm_waist:.2f} — " + (
            "کمتر از ۰٫۳۶، احتمال کم‌توسعه‌بودن عضلهٔ بازو"
            if arm_waist_band == "low"
            else "توسعهٔ نسبی کافی"
        )

    asym = {
        "upper_arm": _asymmetry(m.get("upper_arm_right_cm"), m.get("upper_arm_left_cm")),
        "thigh": _asymmetry(m.get("thigh_right_cm"), m.get("thigh_left_cm")),
        "calf": _asymmetry(m.get("calf_right_cm"), m.get("calf_left_cm")),
    }
    measured_asym = {k: v for k, v in asym.items() if v is not None}
    notable = [k for k, v in measured_asym.items() if v["band"] == "notable"]

    if notable:
        headline = "نامتقارنی محسوس در " + "، ".join(notable)
    elif measured_asym:
        headline = "تقارن چپ/راست در محدودهٔ طبیعی"
    else:
        headline = "برای بررسی تقارن، هر دو سمت باید اندازه‌گیری شود"

    return {
        "ratios": {
            "waist_to_height": {
                "value": whtr,
                "band": whtr_band,
                "reason": whtr_reason,
                "threshold": WHTR_ELEVATED,
            },
            "waist_to_hip": {
                "value": whr,
                "band": whr_band,
                "reason": whr_reason,
                "threshold": WHR_HIGH_MALE if (gender or "").lower() == "male" else WHR_HIGH_FEMALE,
            },
            "arm_to_waist": {
                "value": arm_waist,
                "band": arm_waist_band,
                "reason": arm_waist_reason,
                "threshold": ARM_WAIST_LOW,
            },
        },
        "asymmetry": asym,
        "headline": headline,
        "missing": missing,
        "note": (
            "این تحلیل آنتروپومتریک است، نه ترکیب بدنی سگمنتی. "
            "دادهٔ امپدانس یا InBody در این نسخه استفاده نمی‌شود (D-024)."
        ),
        "rule_version": SEGMENTAL_VERSION,
    }


def trend(points: list[dict]) -> dict | None:
    """روند محیط‌ها بین دو یا چند اندازه‌گیری.

    کمتر از دو نقطه ⇒ `None`. یک نقطه روند نیست و نباید به‌عنوان روند
    نمایش داده شود.
    """
    if len(points) < 2:
        return None
    first, last = points[0], points[-1]

    def delta(key: str) -> float | None:
        a, b = first.get(key), last.get(key)
        if a is None or b is None:
            return None
        return round(b - a, 1)

    days = (last["measured_at"] - first["measured_at"]).days
    changes = {
        k: delta(k)
        for k in (
            "waist_cm",
            "chest_cm",
            "upper_arm_right_cm",
            "thigh_right_cm",
            "calf_right_cm",
        )
    }
    known = {k: v for k, v in changes.items() if v is not None}
    biggest = max(known, key=lambda k: abs(known[k])) if known else None

    if not known:
        headline = "هیچ محیطی در هر دو اندازه‌گیری مشترک نیست"
    elif biggest and abs(known[biggest]) >= 2.0:
        direction = "افزایش" if known[biggest] > 0 else "کاهش"
        headline = f"بیشترین تغییر: {direction} {abs(known[biggest]):.1f} سانتی‌متر در {biggest}"
    else:
        headline = "تغییرات محیطی کمتر از ۲ سانتی‌متر — در محدودهٔ نوسان اندازه‌گیری"

    return {
        "span_days": days,
        "changes_cm": changes,
        "biggest_change": biggest,
        "headline": headline,
        "rule_version": SEGMENTAL_VERSION,
    }

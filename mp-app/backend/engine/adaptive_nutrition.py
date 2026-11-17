"""G3 — تغذیهٔ سازگار: تخمین TDEE از روند وزن واقعی + اصلاح هفتگی (M49-c3).

## مسئله‌ای که حل می‌کند
`engine/nutrition.py` یک TDEE **نظری** از فرمول Mifflin می‌دهد. آن فرمول
خطای ±۱۰–۱۵٪ دارد؛ یعنی برای یک عضو ۸۰ کیلویی می‌تواند ۲۵۰–۳۰۰ کالری
خطا داشته باشد — کافی برای اینکه «رژیم» در عمل کار نکند.

راه‌حل استاندارد صنعت (MacroFactor، RP) این است: **مصرف واقعی + تغییر وزن
واقعی ⇒ TDEE واقعی**. چون تغییر وزن، تنها اندازه‌گیری مستقل از فرمول است:

    تغییر انرژی ذخیره‌شده = مصرف − مصرف‌شده
    کیلوگرم چربی ≈ ۷۷۰۰ کیلوکالری
    ⇒ TDEE = میانگین مصرف روزانه − (Δوزن به کیلوگرم × ۷۷۰۰ / تعداد روز)

## تصمیم‌های صریح این ماژول

1. **وزن روند، نه وزن خام.** وزن روزانه ۱–۲ کیلوگرم نوسان آب/گلیکوژن دارد.
   مدل روند از میانگین متحرک وزنی نمایی (EMA) استفاده می‌کند، چون
   میانگین ساده به آخرین هفته وزن بیشتری نمی‌دهد ولی EMA می‌دهد.
2. **حداقل داده.** کمتر از ۷ روز دادهٔ وزن یا کمتر از ۷ روز ثبت غذا ⇒
   `insufficient_data` و TDEE تخمین زده **نمی‌شود**. عدد بی‌پایه بدتر از
   «نمی‌دانم» است.
3. **دقت‌سنجی همراه عدد.** `confidence` بر اساس طول بازه و پراکندگی
   داده محاسبه می‌شود، نه یک برچسب سلیقه‌ای.
4. **اصلاح تدریجی، نه پرش.** پیشنهاد کالری حداکثر ±۱۵٪ از مقدار فعلی
   حرکت می‌کند؛ یک شوک ۵۰۰ کالری هم پایبندی را می‌شکند و هم دادهٔ هفتهٔ
   بعد را آلوده می‌کند.
5. **بدون LLM.** همهٔ اعداد از قواعد قطعی (G8).

نتیجهٔ هر محاسبه `source` و `rule_version` دارد و هیچ عددی بدون منبع نیست.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median

ADAPTIVE_VERSION = "adaptive-nutrition-1.0"

# انرژی یک کیلوگرم بافت: چربی خالص ≈ ۹۴۰۰ kcal/kg، ولی وزن‌کردن معمول
# ترکیبی از چربی و آب و عضله است. ۷۷۰۰ مقدار متعارف صنعت است و همان
# استفاده می‌شود — نه ۹۴۰۰، که TDEE را روی کاغذ بزرگ‌تر نشان می‌دهد.
KCAL_PER_KG = 7700.0

# حداقل داده برای اینکه تخمین معنا داشته باشد
MIN_WEIGHT_DAYS = 14  # ۲ هفته وزن، برای یک شیب با نویز کم
MIN_INTAKE_DAYS = 7  # یک هفته ثبت غذا
MIN_SPAN_DAYS = 14  # بازهٔ زمانی بین اولین و آخرین وزن

# سقف حرکت پیشنهاد نسبت به مقدار فعلی
MAX_STEP_RATIO = 0.15

# EMA وزن: نیمه‌عمر ۷ روز ⇒ نوسان آب در حدود یک هفته صاف می‌شود
EMA_HALF_LIFE_DAYS = 7.0

# مرزهای سلامت روند وزن (کیلوگرم در هفته، نسبت به وزن بدن)
SAFE_LOSS_PCT_PER_WEEK = 1.0  # بیش از ۱٪ در هفته = تحلیل عضله
SAFE_GAIN_PCT_PER_WEEK = 0.5  # بیش از ۰٫۵٪ در هفته = چربی ناخواسته


@dataclass
class WeightTrend:
    """روند وزن: شیب بر حسب کیلوگرم در هفته + کیفیت داده."""

    slope_kg_per_week: float | None
    smoothed_start: float | None
    smoothed_end: float | None
    days_used: int
    span_days: int
    confidence: str  # high | medium | low | insufficient
    reason: str
    rule_version: str = ADAPTIVE_VERSION
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "slope_kg_per_week": (
                None if self.slope_kg_per_week is None else round(self.slope_kg_per_week, 3)
            ),
            "smoothed_start_kg": (
                None if self.smoothed_start is None else round(self.smoothed_start, 2)
            ),
            "smoothed_end_kg": (None if self.smoothed_end is None else round(self.smoothed_end, 2)),
            "days_used": self.days_used,
            "span_days": self.span_days,
            "confidence": self.confidence,
            "reason": self.reason,
            "notes": list(self.notes),
            "rule_version": self.rule_version,
        }


def _to_ordinal(date_str: str) -> int:
    """YYYY-MM-DD ⇒ عدد روز (برای خطی‌سازی زمان)."""
    from datetime import date

    y, m, d = (int(x) for x in date_str.split("-"))
    return date(y, m, d).toordinal()


def ema_weights(
    points: list[tuple[str, float]], half_life_days: float = EMA_HALF_LIFE_DAYS
) -> list[tuple[int, float]]:
    """EMA وزن بر حسب روز — خروجی (روز, وزن صاف‌شده).

    چرا EMA و نه میانگین ساده: میانگین ساده به همهٔ روزها وزن یکسان می‌دهد،
    ولی برای *تشخیص روند* وزن روزهای نزدیک‌تر مهم‌ترند. نیمه‌عمر ۷ روز
    یعنی وزن دیروز دو برابر ۷ روز پیش اهمیت دارد.
    """
    if not points:
        return []
    ordered = sorted(points, key=lambda p: _to_ordinal(p[0]))
    alpha = 1 - 0.5 ** (1.0 / half_life_days)
    out: list[tuple[int, float]] = []
    prev_day: int | None = None
    current: float | None = None
    for date_str, weight in ordered:
        day = _to_ordinal(date_str)
        if current is None:
            current = float(weight)
        else:
            # فاصلهٔ واقعی بین اندازه‌گیری‌ها را در آلفا لحاظ می‌کنیم؛
            # وگرنه اندازه‌گیری‌های نامنظم وزن اشتباه می‌گیرند.
            gap = max(1, day - prev_day) if prev_day is not None else 1
            a = 1 - (1 - alpha) ** gap
            current = current + a * (float(weight) - current)
        out.append((day, current))
        prev_day = day
    return out


def weight_trend(points: list[tuple[str, float]]) -> WeightTrend:
    """روند وزن از فهرست (تاریخ, وزن). دادهٔ کم ⇒ «نمی‌دانم»، نه صفر."""
    if len(points) < MIN_WEIGHT_DAYS:
        return WeightTrend(
            slope_kg_per_week=None,
            smoothed_start=None,
            smoothed_end=None,
            days_used=len(points),
            span_days=0,
            confidence="insufficient",
            reason=(
                f"فقط {len(points)} اندازه‌گیری وزن ثبت شده؛ حداقل "
                f"{MIN_WEIGHT_DAYS} لازم است — روند محاسبه نشد"
            ),
        )

    smoothed = ema_weights(points)
    span = smoothed[-1][0] - smoothed[0][0]
    if span < MIN_SPAN_DAYS:
        return WeightTrend(
            slope_kg_per_week=None,
            smoothed_start=smoothed[0][1],
            smoothed_end=smoothed[-1][1],
            days_used=len(points),
            span_days=span,
            confidence="insufficient",
            reason=(f"بازهٔ اندازه‌گیری {span} روز است؛ حداقل {MIN_SPAN_DAYS} روز لازم است"),
        )

    # شیب از OLS روی **دادهٔ خام**، نه روی EMA.
    #
    # کشف با آزمون زمینِ معلوم: شیب واقعی −۰٫۵ کیلوگرم/هفته تزریق شد و
    # رگرسیون روی EMA مقدار −۰٫۳۵ برگرداند — کم‌برآورد ۳۰٪. دلیل: EMA در
    # ابتدای بازه از مقدار اول شروع می‌کند و تا «قفل شدن» عقب است، پس
    # خطای سیستماتیک به شیب تزریق می‌کند. OLS روی دادهٔ خام برای یک روند
    # خطی + نویز، برآورد نااریب می‌دهد؛ EMA فقط برای نمایش روند می‌ماند.
    raw = sorted(points, key=lambda p: _to_ordinal(p[0]))
    n = len(raw)
    xs = [_to_ordinal(d) for d, _ in raw]
    ys = [float(w) for _, w in raw]
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys, strict=True))
    den = sum((x - mean_x) ** 2 for x in xs)
    slope_per_day = 0.0 if den == 0 else num / den
    slope_week = slope_per_day * 7

    # پراکندگی باقی‌مانده‌ها ⇒ کیفیت داده (وزن پرنوسان = شیب نامطمئن)
    residuals = [
        abs(y - (mean_y + slope_per_day * (x - mean_x))) for x, y in zip(xs, ys, strict=True)
    ]
    noise = median(residuals) if residuals else 0.0

    if span >= 28 and noise <= 0.4:
        confidence = "high"
    elif span >= 21 and noise <= 0.8:
        confidence = "medium"
    else:
        confidence = "low"

    notes = []
    if noise > 1.0:
        notes.append(
            f"پراکندگی وزن بالا است (میانهٔ انحراف {noise:.2f} کیلوگرم) — "
            "وزن‌کشی در ساعت ثابت و ناشتا توصیه می‌شود"
        )

    return WeightTrend(
        slope_kg_per_week=slope_week,
        smoothed_start=smoothed[0][1],
        smoothed_end=smoothed[-1][1],
        days_used=len(points),
        span_days=span,
        confidence=confidence,
        reason=(
            f"شیب روند {slope_week:+.2f} کیلوگرم در هفته از {len(points)} "
            f"اندازه‌گیری در {span} روز (اطمینان: {confidence})"
        ),
        notes=notes,
    )


def estimate_tdee(
    *,
    weight_points: list[tuple[str, float]],
    intake_by_date: dict[str, float],
    current_target_kcal: int | None = None,
) -> dict:
    """TDEE واقعی از مصرف و تغییر وزن.

    `intake_by_date`: {YYYY-MM-DD: کالری ثبت‌شده}. **فقط روزهایی که غذا ثبت
    شده‌اند** استفاده می‌شوند — روز ثبت‌نشده را صفر نمی‌گیریم، چون صفر یعنی
    «نخورده» و این بزرگ‌ترین منبع خطا در تمام اپ‌های تغذیه است.
    """
    trend = weight_trend(weight_points)

    logged_days = {d: v for d, v in intake_by_date.items() if v is not None and v > 0}
    if len(logged_days) < MIN_INTAKE_DAYS:
        return {
            "tdee_kcal": None,
            "confidence": "insufficient",
            "data_state": "insufficient_intake",
            "reason": (
                f"فقط {len(logged_days)} روز ثبت غذا وجود دارد؛ حداقل "
                f"{MIN_INTAKE_DAYS} روز لازم است — TDEE تخمین زده نشد"
            ),
            "mean_intake_kcal": round(sum(logged_days.values()) / len(logged_days), 1)
            if logged_days
            else None,
            "trend": trend.to_dict(),
            "rule_version": ADAPTIVE_VERSION,
        }

    if trend.slope_kg_per_week is None:
        return {
            "tdee_kcal": None,
            "confidence": "insufficient",
            "data_state": "insufficient_weight",
            "reason": trend.reason,
            "mean_intake_kcal": round(sum(logged_days.values()) / len(logged_days), 1),
            "trend": trend.to_dict(),
            "rule_version": ADAPTIVE_VERSION,
        }

    mean_intake = sum(logged_days.values()) / len(logged_days)
    daily_delta = (trend.slope_kg_per_week * KCAL_PER_KG) / 7
    tdee_kcal = mean_intake - daily_delta

    # کیفیت تخمین = کیفیت دادهٔ وزن، با تنزل اگر ثبت غذا کم است
    confidence = trend.confidence
    if len(logged_days) < MIN_INTAKE_DAYS * 2 and confidence == "high":
        confidence = "medium"

    return {
        "tdee_kcal": round(tdee_kcal, 1),
        "confidence": confidence,
        "data_state": "estimated",
        "mean_intake_kcal": round(mean_intake, 1),
        "weight_change_kcal_per_day": round(daily_delta, 1),
        "reason": (
            f"میانگین مصرف {mean_intake:.0f} کالری در {len(logged_days)} روز ثبت‌شده، "
            f"روند وزن {trend.slope_kg_per_week:+.2f} کیلوگرم/هفته ⇒ "
            f"TDEE ≈ {tdee_kcal:.0f} کالری"
        ),
        "trend": trend.to_dict(),
        "assumptions": [
            f"هر کیلوگرم تغییر وزن ≈ {KCAL_PER_KG:.0f} کیلوکالری",
            "فقط روزهای ثبت‌شده در میانگین مصرف حساب شده‌اند",
            "وزن صاف‌شده با EMA (نیمه‌عمر ۷ روز) تا نوسان آب اثر نگذارد",
        ],
        "rule_version": ADAPTIVE_VERSION,
    }


def suggest_calorie_adjustment(
    *,
    tdee_kcal: float | None,
    current_target_kcal: int | None,
    goal: str,
    body_weight_kg: float | None,
    slope_kg_per_week: float | None,
) -> dict:
    """پیشنهاد اصلاح کالری — با سقف گام و بررسی سلامت روند.

    منطق: هدف بین TDEE و هدف کاهش/افزایش تنظیم می‌شود، ولی هرگز بیش از
    ±۱۵٪ در یک هفته جابه‌جا نمی‌شود. اگر روند وزن از مرز سلامت گذشته باشد،
    اول آن اصلاح می‌شود — نه اینکه کالری بیشتر کم کنیم.
    """
    goal_multiplier = {
        "hypertrophy": 1.10,
        "strength": 1.05,
        "weight_loss": 0.85,
        "fitness": 1.0,
    }
    if goal not in goal_multiplier:
        return {
            "suggested_target_kcal": current_target_kcal,
            "delta_kcal": 0,
            "action": "none",
            "reason": f"هدف «{goal}» در جدول قواعد نیست — تغییری اعمال نمی‌شود",
            "rule_version": ADAPTIVE_VERSION,
        }

    if tdee_kcal is None or current_target_kcal is None:
        return {
            "suggested_target_kcal": current_target_kcal,
            "delta_kcal": 0,
            "action": "none",
            "reason": "TDEE یا هدف فعلی نامعلوم است — اصلاحی پیشنهاد نمی‌شود",
            "rule_version": ADAPTIVE_VERSION,
        }

    # ۱) مرز سلامت روند وزن مقدم بر هر اصلاح کالری است
    if slope_kg_per_week is not None and body_weight_kg:
        weekly_pct = (slope_kg_per_week / body_weight_kg) * 100
        if goal in ("weight_loss", "fitness") and weekly_pct < -SAFE_LOSS_PCT_PER_WEEK:
            return {
                "suggested_target_kcal": round(current_target_kcal * 1.10),
                "delta_kcal": round(current_target_kcal * 0.10),
                "action": "increase",
                "reason": (
                    f"کاهش وزن {abs(weekly_pct):.2f}٪ در هفته از مرز "
                    f"{SAFE_LOSS_PCT_PER_WEEK}٪ گذشته — خطر تحلیل عضله؛ "
                    "کالری افزایش می‌یابد، نه کاهش"
                ),
                "rule_version": ADAPTIVE_VERSION,
            }
        if goal == "hypertrophy" and weekly_pct > SAFE_GAIN_PCT_PER_WEEK:
            return {
                "suggested_target_kcal": round(current_target_kcal * 0.90),
                "delta_kcal": -round(current_target_kcal * 0.10),
                "action": "decrease",
                "reason": (
                    f"افزایش وزن {weekly_pct:.2f}٪ در هفته از مرز "
                    f"{SAFE_GAIN_PCT_PER_WEEK}٪ گذشته — بیشترش چربی است؛ "
                    "کالری کاهش می‌یابد"
                ),
                "rule_version": ADAPTIVE_VERSION,
            }

    # ۲) هدف ایده‌آل از TDEE
    ideal = tdee_kcal * goal_multiplier[goal]
    raw_delta = ideal - current_target_kcal

    # ۳) سقف گام: هرگز بیش از ۱۵٪ در یک هفته
    max_step = current_target_kcal * MAX_STEP_RATIO
    if abs(raw_delta) < 50:
        return {
            "suggested_target_kcal": current_target_kcal,
            "delta_kcal": 0,
            "action": "keep",
            "reason": (
                f"هدف فعلی {current_target_kcal} با هدف ایده‌آل {ideal:.0f} "
                "تفاوت معنادار ندارد — تغییری لازم نیست"
            ),
            "rule_version": ADAPTIVE_VERSION,
        }
    clamped = max(-max_step, min(max_step, raw_delta))
    suggested = round(current_target_kcal + clamped)

    return {
        "suggested_target_kcal": suggested,
        "delta_kcal": suggested - current_target_kcal,
        "action": "increase" if clamped > 0 else "decrease",
        "ideal_target_kcal": round(ideal),
        "capped": abs(raw_delta) > max_step,
        "reason": (
            f"TDEE واقعی {tdee_kcal:.0f} × ضریب «{goal}» = {ideal:.0f}؛ "
            f"هدف فعلی {current_target_kcal} ⇒ "
            + (
                f"حرکت {clamped:+.0f} کالری (سقف ۱۵٪ در هفته اعمال شد)"
                if abs(raw_delta) > max_step
                else f"حرکت {clamped:+.0f} کالری"
            )
        ),
        "rule_version": ADAPTIVE_VERSION,
    }

"""G13 — مدل آمادگی/خستگی: کاهش خودکار حجم بر پایهٔ چند سیگنال (M50-c3).

## تفاوت با G1
`engine/set_feedback.py` فقط **درد عضلانی** را می‌بیند و اگر ≥۷ بود یک ست
کم می‌کند. ولی خستگی واقعی چند نشانه دارد و درد یکی از ضعیف‌ترین‌هاست:

  * **افت تکرار در بار ثابت** — قوی‌ترین نشانهٔ خستگی عصبی-عضلانی.
  * **RIR واقعی بالاتر از هدف** — ست‌ها آسان شده‌اند؛ یعنی بار سبک است،
    نه اینکه athlete آماده است.
  * **RIR واقعی پایین‌تر از هدف** — ست‌ها سخت‌تر از تجویز شده‌اند؛
    خستگی انباشته.
  * **بار تمرینی هفتگی** (sets × بار نسبی) که پرش ناگهانی داشته.
  * **درد** که G1 از قبل دارد ولی تنها سیگنال نیست.

این ماژول سیگنال‌ها را جمع می‌زند و یک **امتیاز آمادگی ۰..۱۰۰** می‌دهد.
امتیاز بالا = آماده (می‌توان حجم را حفظ/افزایش داد)، پایین = خسته
(حجم باید خودکار کم شود).

## تصمیم‌های صریح
1. **وزن‌های ثابت و مستند، نه شبکهٔ عصبی.** پروژهٔ پژوهشی است و هر عدد
   باید قابل دفاع باشد؛ یک مدل جعبه‌سیاه برای داوری پایان‌نامه ارزش ندارد.
2. **سیگنال نامعلوم صفر نمی‌شود.** اگر RIR ثبت نشده باشد، آن سیگنال از
   میانگین حذف می‌شود و در `missing_signals` گزارش می‌گردد؛ وزنش به
   سیگنال‌های موجود توزیع می‌شود.
3. **آستانهٔ قطعی برای اقدام.** فقط وقتی امتیاز زیر `DELOAD_THRESHOLD`
   بیفتد توصیهٔ کاهش حجم می‌شود؛ در غیر این صورت «حفظ».
4. **بدون LLM** (G8) — همهٔ اعداد از قواعد قطعی.
"""

from __future__ import annotations

from dataclasses import dataclass, field

READINESS_VERSION = "readiness-1.0"

# آستانه‌ها
DELOAD_THRESHOLD = 55  # زیر این ⇒ کاهش خودکار حجم
INDICATOR_RECOVERY = 40  # زیر این ⇒ فقط حفظ، نه افزایش

# وزن سیگنال‌ها (جمع = ۱). انتخاب‌ها با ادبیات RPE/autoregulation هم‌راستاست:
# افت تکرار در بار ثابت، معتبرترین شاخص خستگی است؛ درد، ذهنی‌ترین و ضعیف‌ترین.
SIGNAL_WEIGHTS: dict[str, float] = {
    "rep_drop": 0.35,
    "rir_mismatch": 0.25,
    "soreness": 0.20,
    "volume_spike": 0.20,
}

# آستانه‌های عددی هر سیگنال
RIR_TOLERANCE = 1.0  # اختلاف مجاز RIR واقعی از هدف
SORENESS_OK = 3  # تا این حد نرمال
SORENESS_BAD = 8  # از این حد به بالا، بدترین حالت
VOLUME_SPIKE_RATIO = 1.3  # بیش از ۳۰٪ رشد هفتگی = پرش


@dataclass
class Signal:
    """یک سیگنال با کیفیت داده و سهمش در امتیاز نهایی."""

    name: str
    value: float | None  # None = نامعلوم
    score: float | None  # ۰..۱۰۰ (بالا = آماده)
    reason: str
    weight: float = 0.0
    contribution: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "value": None if self.value is None else round(self.value, 2),
            "score": None if self.score is None else round(self.score, 1),
            "reason": self.reason,
        }


@dataclass
class Readiness:
    score: float | None
    band: str  # ready | monitor | fatigued | insufficient
    recommendation: str  # increase | keep | deload | insufficient
    volume_delta_sets: int
    signals: list[Signal] = field(default_factory=list)
    missing_signals: list[str] = field(default_factory=list)
    reason: str = ""
    rule_version: str = READINESS_VERSION

    def to_dict(self) -> dict:
        return {
            "score": None if self.score is None else round(self.score, 1),
            "band": self.band,
            "recommendation": self.recommendation,
            "volume_delta_sets": self.volume_delta_sets,
            "signals": [s.to_dict() for s in self.signals],
            "missing_signals": list(self.missing_signals),
            "reason": self.reason,
            "weights": dict(SIGNAL_WEIGHTS),
            "thresholds": {
                "deload_below": DELOAD_THRESHOLD,
                "recovery_below": INDICATOR_RECOVERY,
                "rir_tolerance": RIR_TOLERANCE,
                "volume_spike_ratio": VOLUME_SPIKE_RATIO,
            },
            "rule_version": self.rule_version,
        }


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def score_rep_drop(
    *, target_reps: int, reps_done: int, rir: float | None, previous_reps: int | None = None
) -> Signal:
    """افت تکرار در بار ثابت — معتبرترین نشانهٔ خستگی.

    اگر `previous_reps` داده شود، افت نسبت به جلسهٔ قبل سنجیده می‌شود
    (مقایسهٔ منصفانه‌تر). وگرنه نسبت به هدف برنامه.
    """
    baseline = previous_reps or target_reps
    if baseline <= 0:
        return Signal("rep_drop", None, None, "هدف تکرار نامعتبر است")
    ratio = reps_done / baseline
    # نسبت ۱.۰ ⇒ ۱۰۰، نسبت ۰.۵ ⇒ ۰
    score = _clamp(ratio * 100)
    if ratio >= 1.0:
        why = f"{reps_done} تکرار از پایهٔ {baseline} — بدون افت"
    elif ratio >= 0.8:
        why = f"{reps_done} از {baseline} تکرار — افت خفیف"
    else:
        why = f"{reps_done} از {baseline} تکرار — افت محسوس، نشانهٔ خستگی"
    return Signal("rep_drop", ratio, score, why)


def score_rir_mismatch(*, target_rir: float | None, actual_rir: float | None) -> Signal:
    """اختلاف RIR واقعی از هدف، در دو جهت.

    RIR بالاتر از هدف (ست آسان) نشانهٔ بار سبک است، نه آمادگی بالا —
    ولی برای «خستگی» خطرناک نیست، پس امتیازش خنثی‌تر است.
    RIR پایین‌تر از هدف (ست سخت‌تر از تجویز) نشانهٔ خستگی انباشته است.
    """
    if target_rir is None or actual_rir is None:
        return Signal("rir_mismatch", None, None, "RIR هدف یا واقعی ثبت نشده")
    diff = actual_rir - target_rir
    if abs(diff) <= RIR_TOLERANCE:
        return Signal("rir_mismatch", diff, 100.0, "RIR واقعی با هدف هم‌خوان است")
    # شیب جریمه: هر واحد RIR سخت‌تر از تجویز، ۳۰ امتیاز؛ هر واحد آسان‌تر، ۱۵.
    #
    # چرا این نسبت: RIR پایین‌تر یعنی ست واقعاً سخت‌تر از برنامه بوده و
    # خستگی انباشته می‌شود (جریمهٔ بالا). RIR بالاتر یعنی بار سبک بوده —
    # برای ریکاوری خطرناک نیست، فقط برنامه بازنگری لازم دارد (جریمهٔ کم).
    # کشف تست: نسخهٔ اول با ۲۵/۱۵ افت ۲ واحدی سخت‌تر را از ۳ واحدی
    # آسان‌تر ملایم‌تر می‌کرد — دقیقاً برعکس ادعای کد.
    per_unit = 15.0 if diff > 0 else 30.0
    excess = abs(diff) - RIR_TOLERANCE
    score = _clamp(100 - excess * per_unit)
    if diff > 0:
        return Signal(
            "rir_mismatch",
            diff,
            score,
            f"RIR {actual_rir} بالاتر از هدف {target_rir} — بار سبک‌تر از تجویز",
        )
    return Signal(
        "rir_mismatch",
        diff,
        score,
        f"RIR {actual_rir} پایین‌تر از هدف {target_rir} — ست‌ها سخت‌تر از تجویز",
    )


def score_soreness(*, soreness: int | None) -> Signal:
    """درد عضلانی ۰..۱۰."""
    if soreness is None:
        return Signal("soreness", None, None, "درد عضلانی ثبت نشده")
    if soreness <= SORENESS_OK:
        return Signal("soreness", soreness, 100.0, f"درد {soreness}/۱۰ — نرمال")
    if soreness >= SORENESS_BAD:
        return Signal("soreness", soreness, 10.0, f"درد {soreness}/۱۰ — شدید")
    # بین ۳ و ۸ خطی
    span = SORENESS_BAD - SORENESS_OK
    score = _clamp(100 - ((soreness - SORENESS_OK) / span) * 90)
    return Signal("soreness", soreness, score, f"درد {soreness}/۱۰ — بالاتر از نرمال")


def score_volume_spike(*, this_week_sets: int, last_week_sets: int) -> Signal:
    """پرش ناگهانی حجم هفتگی.

    رشد تدریجی (۱۰–۲۰٪) طبیعی است؛ پرش بیش از ۳۰٪ معمولاً باعث خستگی
    انباشته می‌شود و همان جایی است که اتورگولیشن باید ترمز بکشد.
    """
    if last_week_sets <= 0:
        return Signal("volume_spike", None, None, "حجم هفتهٔ قبل نامعلوم است")
    ratio = this_week_sets / last_week_sets
    if ratio <= VOLUME_SPIKE_RATIO:
        return Signal("volume_spike", ratio, 100.0, f"حجم {ratio:.2f}× هفتهٔ قبل — در محدوده")
    excess = ratio - VOLUME_SPIKE_RATIO
    score = _clamp(100 - excess * 200)
    return Signal(
        "volume_spike",
        ratio,
        score,
        f"حجم {ratio:.2f}× هفتهٔ قبل — پرش بیش از {VOLUME_SPIKE_RATIO:.1f}× (خستگی انباشته)",
    )


def assess_readiness(
    *,
    target_reps: int,
    reps_done: int,
    target_rir: float | None = None,
    actual_rir: float | None = None,
    soreness: int | None = None,
    this_week_sets: int = 0,
    last_week_sets: int = 0,
    previous_reps: int | None = None,
) -> Readiness:
    """امتیاز آمادگی ۰..۱۰۰ + توصیهٔ قطعی.

    وزن سیگنال‌های نامعلوم به سیگنال‌های موجود توزیع می‌شود — نه اینکه
    صفر حساب شوند (که امتیاز را بی‌دلیل پایین می‌آورد).
    """
    signals = [
        score_rep_drop(
            target_reps=target_reps,
            reps_done=reps_done,
            rir=actual_rir,
            previous_reps=previous_reps,
        ),
        score_rir_mismatch(target_rir=target_rir, actual_rir=actual_rir),
        score_soreness(soreness=soreness),
        score_volume_spike(this_week_sets=this_week_sets, last_week_sets=last_week_sets),
    ]

    known = [s for s in signals if s.score is not None]
    missing = [s.name for s in signals if s.score is None]

    if not known:
        return Readiness(
            score=None,
            band="insufficient",
            recommendation="insufficient",
            volume_delta_sets=0,
            signals=signals,
            missing_signals=missing,
            reason="هیچ سیگنال قابل استفاده‌ای ثبت نشده — امتیاز آمادگی ساخته نمی‌شود",
        )

    # وزن‌های موجود را نرمال می‌کنیم تا جمعشان ۱ شود
    total_weight = sum(SIGNAL_WEIGHTS[s.name] for s in known)
    score = 0.0
    for s in known:
        w = SIGNAL_WEIGHTS[s.name] / total_weight
        s.weight = w
        s.contribution = s.score * w
        score += s.contribution

    score = round(score, 1)

    if score < DELOAD_THRESHOLD:
        band = "fatigued"
        recommendation = "deload"
        delta = -1
        reason = (
            f"امتیاز آمادگی {score} زیر آستانهٔ {DELOAD_THRESHOLD} است — "
            "حجم خودکار یک ست کاهش می‌یابد"
        )
    elif score < INDICATOR_RECOVERY:
        band = "monitor"
        recommendation = "keep"
        delta = 0
        reason = f"امتیاز آمادگی {score} در ناحیهٔ مراقبت — حجم حفظ می‌شود، بیشتر نمی‌شود"
    else:
        band = "ready"
        recommendation = "keep"
        delta = 0
        reason = f"امتیاز آمادگی {score} — بازیابی کافی، حجم حفظ می‌شود"

    if missing:
        reason += f"؛ سیگنال نامعلوم: {', '.join(missing)}"

    return Readiness(
        score=score,
        band=band,
        recommendation=recommendation,
        volume_delta_sets=delta,
        signals=signals,
        missing_signals=missing,
        reason=reason,
    )

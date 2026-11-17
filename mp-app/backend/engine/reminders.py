"""موتور یادآوری — reminders-1.0 (G11).

## چرا موتور، نه یک cron ساده
یادآوری در باشگاه چند نوع دارد: تمدید عضویت، جلسهٔ تمرین، ارزیابی دوره‌ای،
و پرداخت معوق. هر کدام **مبنای زمانی متفاوت** دارند. اگر همه را در یک
تابع بنویسیم، هر قاعدهٔ جدید کد قبلی را می‌شکند. پس هر یادآوری یک قاعدهٔ
مستقل با `key`، آستانه، و دلیل است.

## قاعدهٔ صادقانه
اگر دادهٔ لازم برای تصمیم نیست (مثلاً تاریخ پایان عضویت نامعلوم است)،
یادآوری ساخته نمی‌شود و علتش گزارش می‌گردد. «هیچ یادآوری» با «داده
نامعلوم» یکی نیست و در خروجی تفکیک می‌شوند.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

REMINDER_VERSION = "reminders-1.0"

# چند روز قبل از انقضای عضویت یادآوری شود
RENEWAL_LEAD_DAYS = 7
# اگر بیش از این تعداد روز از آخرین تمرین گذشته باشد
INACTIVITY_DAYS = 10
# فاصلهٔ پیشنهادی ارزیابی مجدد
REASSESS_DAYS = 90


def _days_until(target: datetime | None, now: datetime) -> int | None:
    if target is None:
        return None
    if target.tzinfo is None:
        target = target.replace(tzinfo=UTC)
    return (target - now).days


def plan(
    *,
    now: datetime | None = None,
    membership_end: datetime | None = None,
    last_workout_at: datetime | None = None,
    last_assessment_at: datetime | None = None,
    pending_amount_rial: int = 0,
) -> dict:
    """فهرست یادآوری‌های لازم + دلیلِ هر یادآوریِ ساخته‌نشده.

    خروجی خالص است (بدون DB) تا قابل تست و قابل بازتولید باشد.
    """
    now = now or datetime.now(UTC)
    due: list[dict] = []
    skipped: list[dict] = []

    # ۱. تمدید عضویت
    if membership_end is None:
        skipped.append({"key": "renewal", "reason": "تاریخ پایان عضویت ثبت نشده"})
    else:
        days = _days_until(membership_end, now)
        if days is None:
            skipped.append({"key": "renewal", "reason": "تاریخ پایان نامعلوم"})
        elif 0 <= days <= RENEWAL_LEAD_DAYS:
            due.append(
                {
                    "key": "renewal",
                    "priority": "high" if days <= 2 else "normal",
                    "title": "تمدید عضویت",
                    "body": f"عضویت شما {days} روز دیگر به پایان می‌رسد.",
                    "due_in_days": days,
                    "rule": f"membership_end - now <= {RENEWAL_LEAD_DAYS}d",
                }
            )
        elif days < 0:
            due.append(
                {
                    "key": "renewal_expired",
                    "priority": "high",
                    "title": "عضویت منقضی شده",
                    "body": f"عضویت شما {abs(days)} روز پیش به پایان رسید.",
                    "due_in_days": days,
                    "rule": "membership_end < now",
                }
            )

    # ۲. بی‌تحرکی
    if last_workout_at is None:
        skipped.append({"key": "inactivity", "reason": "هیچ جلسهٔ تمرینی ثبت نشده"})
    else:
        gap = abs(_days_until(last_workout_at, now) or 0)
        if gap >= INACTIVITY_DAYS:
            due.append(
                {
                    "key": "inactivity",
                    "priority": "normal",
                    "title": "برگشت به تمرین",
                    "body": f"{gap} روز از آخرین تمرین گذشته است. یک جلسهٔ سبک شروع خوبی است.",
                    "due_in_days": 0,
                    "rule": f"days_since_last_workout >= {INACTIVITY_DAYS}",
                }
            )

    # ۳. ارزیابی مجدد
    if last_assessment_at is None:
        skipped.append({"key": "reassessment", "reason": "هیچ ارزیابی ثبت نشده"})
    else:
        gap = abs(_days_until(last_assessment_at, now) or 0)
        if gap >= REASSESS_DAYS:
            due.append(
                {
                    "key": "reassessment",
                    "priority": "normal",
                    "title": "ارزیابی دوره‌ای",
                    "body": f"{gap} روز از آخرین ارزیابی گذشته است.",
                    "due_in_days": 0,
                    "rule": f"days_since_last_assessment >= {REASSESS_DAYS}",
                }
            )

    # ۴. پرداخت معوق
    if pending_amount_rial > 0:
        due.append(
            {
                "key": "payment_due",
                "priority": "high",
                "title": "پرداخت معوق",
                "body": f"مبلغ معوق: {pending_amount_rial:,} ریال",
                "due_in_days": 0,
                "rule": "pending_amount_rial > 0",
            }
        )

    order = {"high": 0, "normal": 1}
    due.sort(key=lambda d: (order.get(d["priority"], 2), d.get("due_in_days", 0)))

    return {
        "generated_at": now.isoformat(),
        "reminders": due,
        "skipped": skipped,
        "counts": {"due": len(due), "skipped": len(skipped)},
        "thresholds": {
            "renewal_lead_days": RENEWAL_LEAD_DAYS,
            "inactivity_days": INACTIVITY_DAYS,
            "reassess_days": REASSESS_DAYS,
        },
        "rule_version": REMINDER_VERSION,
    }


def next_run_delay_seconds(now: datetime | None = None) -> int:
    """فاصله تا اجرای بعدی زمان‌بند (ثابت ۶ ساعت، مستند و قابل تست).

    مقدار ثابت است چون «هر ۶ ساعت» تصمیم محصولی است، نه محاسبهٔ ریاضی.
    """
    return 6 * 60 * 60


def window(now: datetime | None = None) -> tuple[datetime, datetime]:
    """بازهٔ اجرای بعدی — برای گزارش و تست idempotency."""
    now = now or datetime.now(UTC)
    return now, now + timedelta(seconds=next_run_delay_seconds(now))

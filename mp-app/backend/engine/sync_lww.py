"""حل تعارض همگام‌سازی با Last-Write-Wins — lww-1.0 (G7).

## چرا LWW و نه چیز پیچیده‌تر
برنامهٔ آفلاین موبایل: کاربر در باشگاه بدون اینترنت بازخورد ست ثبت می‌کند.
تعارض واقعی فقط یک شکل دارد: **همان رکورد در دو دستگاه**. برای این حالت،
LWW با timestamp سمت کلاینت استاندارد صنعتی است (Firebase, CouchDB).
CRDT کامل برای این حجم، پیچیدگی بی‌فایده است.

## تلهٔ LWW که باید صریح مدیریت شود
۱. **ساعت کلاینت دروغ می‌گوید.** اگر یک دستگاه ساعتش عقب باشد، نوشته‌هایش
   همیشه می‌بازند. راه‌حل: `server_received_at` نگه داشته می‌شود و اگر
   ساعت کلاینت بیش از `MAX_CLOCK_SKEW` از سرور جلو باشد، رد می‌شود.
۲. **تعارض واقعی باید گزارش شود، نه بی‌صدا.** کاربر باید بداند نوشته‌اش
   کنار گذاشته شد.
۳. **مساوی بودن timestamp.** مقایسهٔ `>=` با برندهٔ تصادفی، داده را گم
   می‌کند. tie-break قطعی: شناسهٔ دستگاه به‌عنوان مقایسهٔ نهایی.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

LWW_VERSION = "lww-1.0"

# حداکثر اختلاف مجاز ساعت کلاینت با سرور
MAX_CLOCK_SKEW = timedelta(minutes=5)


@dataclass
class Versioned:
    """یک رکورد نسخه‌دار."""

    entity: str
    entity_key: str
    updated_at: datetime
    device_id: str
    payload: dict = field(default_factory=dict)


def _normalize(dt: datetime) -> datetime:
    return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)


def resolve(
    server: Versioned | None,
    client: Versioned,
    *,
    server_now: datetime | None = None,
) -> dict:
    """تصمیم LWW برای یک رکورد.

    خروجی `action` یکی از:
      • `accept` — نوشتهٔ کلاینت برنده شد (سرور خالی بود یا قدیمی‌تر)
      • `reject_stale` — سرور جدیدتر است؛ نوشتهٔ کلاینت کنار گذاشته می‌شود
      • `reject_clock_skew` — ساعت کلاینت غیرقابل‌اعتماد است
      • `conflict_resolved` — دو نوشتهٔ تقریباً هم‌زمان، با tie-break قطعی
    """
    server_now = _normalize(server_now or datetime.now(UTC))
    client_time = _normalize(client.updated_at)

    if client_time - server_now > MAX_CLOCK_SKEW:
        return {
            "entity": client.entity,
            "entity_key": client.entity_key,
            "action": "reject_clock_skew",
            "winner": "server" if server else None,
            "client_time": client_time.isoformat(),
            "server_now": server_now.isoformat(),
            "skew_seconds": int((client_time - server_now).total_seconds()),
            "reason": (
                f"ساعت دستگاه {int((client_time - server_now).total_seconds())} ثانیه "
                f"جلوتر از سرور است — نوشته قابل اعتماد نیست"
            ),
            "rule_version": LWW_VERSION,
        }

    if server is None:
        return {
            "entity": client.entity,
            "entity_key": client.entity_key,
            "action": "accept",
            "winner": "client",
            "reason": "رکورد در سرور وجود نداشت",
            "rule_version": LWW_VERSION,
        }

    server_time = _normalize(server.updated_at)
    delta = (client_time - server_time).total_seconds()

    if client_time > server_time:
        action, winner = "accept", "client"
        reason = f"نوشتهٔ کلاینت {int(delta)} ثانیه جدیدتر است"
    elif client_time < server_time:
        action, winner = "reject_stale", "server"
        reason = f"نوشتهٔ سرور {int(abs(delta))} ثانیه جدیدتر است"
    else:
        # تساوی کامل timestamp یعنی «همان نوشته با همان زمان» — در عمل
        # یعنی تلاش مجدد شبکه، نه تعارض واقعی. اگر همان دستگاه باشد،
        # نوشته بی‌اثر است. tie-break هرگز بر پایهٔ مقایسهٔ رشتهٔ خالی
        # نیست، وگرنه یک نوشتهٔ تکراری «جدید» تلقی و دوباره اعمال می‌شد.
        if client.device_id and client.device_id == server.device_id:
            winner = "server"
            action = "conflict_resolved"
            reason = "timestamp یکسان از همان دستگاه — تلاش مجدد، بی‌اثر"
        else:
            winner = "client" if client.device_id > server.device_id else "server"
            action = "conflict_resolved"
            reason = f"timestamp یکسان؛ برنده با شناسهٔ دستگاه تعیین شد ({winner})"

    return {
        "entity": client.entity,
        "entity_key": client.entity_key,
        "action": action,
        "winner": winner,
        "client_time": client_time.isoformat(),
        "server_time": server_time.isoformat(),
        "delta_seconds": int(delta),
        "reason": reason,
        "client_payload": client.payload if winner == "client" else None,
        "rule_version": LWW_VERSION,
    }


def resolve_batch(
    server_rows: dict[tuple[str, str], Versioned],
    client_rows: list[Versioned],
    *,
    server_now: datetime | None = None,
) -> dict:
    """حل دسته‌ای — برای ارسال صف آفلاین در یک درخواست."""
    results = []
    applied = 0
    rejected = 0
    for row in client_rows:
        key = (row.entity, row.entity_key)
        r = resolve(server_rows.get(key), row, server_now=server_now)
        results.append(r)
        if r["action"] in ("accept", "conflict_resolved") and r["winner"] == "client":
            applied += 1
        else:
            rejected += 1
    return {
        "results": results,
        "counts": {"received": len(client_rows), "applied": applied, "rejected": rejected},
        "rule_version": LWW_VERSION,
    }

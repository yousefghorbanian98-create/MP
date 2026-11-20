"""اجرای یک دور outbox — برای cron/worker یا دستی.

    python -m jobs.outbox_relay            # یک دور
    python -m jobs.outbox_relay --loop 30  # هر ۳۰ ثانیه

handler پیش‌فرض فقط لاگ می‌کند؛ اتصال واقعی push/SMS در این مخزن شاهد اجرایی
ندارد (`BLOCKED`) و باید در لایهٔ زیرساخت وصل شود.
"""

from __future__ import annotations

import argparse
import contextvars
import time

from app.logging import get_logger
from db.base import get_session_factory
from modules.outbox import health as outbox_health
from modules.outbox.inbox import consume_once
from modules.outbox.service import reclaim_stale, relay_once

log = get_logger("outbox_relay")

_current_session: contextvars.ContextVar = contextvars.ContextVar("relay_session", default=None)


def handle(event) -> None:
    """مصرف‌کنندهٔ نمونه: اثر واقعی ندارد، ولی از inbox رد می‌شود تا تحویل
    تکراری بی‌اثر بماند. اتصال اثر واقعی (push/SMS) `BLOCKED` است."""
    key = event.dedup_key or f"outbox-{event.id}"
    consume_once(
        _current_session.get(),
        topic=event.topic,
        dedup_key=key,
        handler=lambda: log.info("outbox_consumed", topic=event.topic, event_id=event.id),
        commit=False,
    )


def run_once() -> dict:
    with get_session_factory()() as db:
        _current_session.set(db)
        try:
            reclaimed = reclaim_stale(db)
            db.commit()
            result = relay_once(db, handler=handle)
            result["reclaimed"] = reclaimed
            # QF-27: heartbeat حتی وقتی صف خالی است، «زنده‌ام» را می‌گوید.
            outbox_health.heartbeat(db, worker_key="outbox", result=result)
            outbox_health.refresh_metrics(db)
            db.commit()
            return result
        finally:
            _current_session.set(None)


def main() -> None:
    parser = argparse.ArgumentParser(description="outbox relay")
    parser.add_argument("--loop", type=int, default=0, metavar="SECONDS")
    args = parser.parse_args()
    while True:
        result = run_once()
        log.info("outbox_relay_cycle", **result)
        if args.loop <= 0:
            return
        time.sleep(args.loop)


if __name__ == "__main__":
    main()

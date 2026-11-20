"""اجرای یک دور outbox — برای cron/worker یا دستی.

    python -m jobs.outbox_relay            # یک دور
    python -m jobs.outbox_relay --loop 30  # هر ۳۰ ثانیه

handler پیش‌فرض فقط لاگ می‌کند؛ اتصال واقعی push/SMS در این مخزن شاهد اجرایی
ندارد (`BLOCKED`) و باید در لایهٔ زیرساخت وصل شود.
"""

from __future__ import annotations

import argparse
import time

from app.logging import get_logger
from db.base import get_session_factory
from modules.outbox.service import reclaim_stale, relay_once

log = get_logger("outbox_relay")


def run_once() -> dict:
    with get_session_factory()() as db:
        reclaimed = reclaim_stale(db)
        db.commit()
        result = relay_once(db)
        db.commit()
        result["reclaimed"] = reclaimed
        return result


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

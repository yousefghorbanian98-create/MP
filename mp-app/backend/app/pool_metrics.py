"""مشاهده‌پذیری استخر اتصال DB — WP 2.2 / F‑04 (D‑13).

- گیج‌ها: `mp_db_pool_size`، `mp_db_pool_checkedout`، `mp_db_pool_overflow`
  (با `publish_pool_gauges` در هر checkout و هر scrape به‌روز می‌شوند؛ checkin
  در SQLAlchemy قبل از برگشت به استخر فراخوانی می‌شود، پس شمارش فقط در scrape دقیق است).
- histogram: `mp_db_connection_held_seconds` (مدت نگه‌داشتن اتصال، در checkin).
- اشباع: `pool_saturated` وقتی `checkedout ≥ 0.9 × ظرفیت` پیوسته ۱۰ ثانیه ادامه یابد.
"""

from __future__ import annotations

import time

from sqlalchemy import event

SATURATION_RATIO = 0.9
SATURATION_WINDOW_SECONDS = 10.0

_saturated_since: dict[str, float] = {}


def _capacity(pool) -> int:
    # QueuePool فقط: ظرفیت = pool_size + max_overflow (ویژگی خصوصی SQLAlchemy).
    max_overflow = getattr(pool, "_max_overflow", None)
    if max_overflow is None or not hasattr(pool, "size"):
        return 0
    return int(pool.size()) + int(max_overflow)


def publish_pool_gauges(engine, metrics) -> None:
    pool = engine.pool
    if not hasattr(pool, "checkedout"):
        return
    metrics.set_gauge("mp_db_pool_size", float(pool.size()))
    metrics.set_gauge("mp_db_pool_checkedout", float(pool.checkedout()))
    # overflow() در SQLAlchemy وقتی زیر pool_size هستیم منفی است؛ گیج را از صفر می‌گیریم.
    metrics.set_gauge("mp_db_pool_overflow", float(max(0, pool.overflow())))


def install_pool_metrics(engine, metrics) -> None:
    """listenerهای checkout/checkin را روی استخر engine ثبت می‌کند (یک‌بار برای هر engine)."""
    pool = engine.pool

    def _on_checkout(_dbapi_conn, record, _proxy) -> None:
        record.info["mp_checked_out_at"] = time.monotonic()

    def _on_checkin(_dbapi_conn, record) -> None:
        started = record.info.pop("mp_checked_out_at", None)
        if started is not None:
            metrics.observe("mp_db_connection_held_seconds", time.monotonic() - started)

    event.listen(pool, "checkout", _on_checkout)
    event.listen(pool, "checkin", _on_checkin)
    publish_pool_gauges(engine, metrics)


def pool_saturated(engine, *, key: str | None = None, now: float | None = None) -> bool:
    """True وقتی اشباع (≥ ۹۰٪ ظرفیت) پیوسته ≥ ۱۰ ثانیه ادامه داشته باشد."""
    pool = engine.pool
    capacity = _capacity(pool)
    if capacity <= 0 or not hasattr(pool, "checkedout"):
        return False
    state_key = key if key is not None else str(id(engine))
    current = time.monotonic() if now is None else now
    if pool.checkedout() >= SATURATION_RATIO * capacity:
        since = _saturated_since.setdefault(state_key, current)
        return current - since >= SATURATION_WINDOW_SECONDS
    _saturated_since.pop(state_key, None)
    return False

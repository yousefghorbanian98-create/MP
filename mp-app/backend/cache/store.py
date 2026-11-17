"""لایهٔ کش — Valkey (سازگار با Redis) با fallback درون‌حافظه‌ای.

قانون (لایهٔ ۱۲): کش دادهٔ کاربرمحور فقط با invalidation صریح — هرگز کش قدیمی نمایش داده نشود.
"""

from __future__ import annotations

import json
import threading
import time
from typing import Any, Protocol


class CacheBackend(Protocol):
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any, ttl: int = 60) -> None: ...
    def invalidate(self, *keys: str) -> None: ...
    def invalidate_prefix(self, prefix: str) -> None: ...


class InMemoryCache:
    """کش درون‌حافظه‌ای (dev/test یا fallback وقتی Valkey در دسترس نیست)."""

    def __init__(self):
        self._data: dict[str, tuple[Any, float | None]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            value, expires = item
            if expires is not None and time.time() > expires:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        with self._lock:
            self._data[key] = (value, time.time() + ttl if ttl else None)

    def invalidate(self, *keys: str) -> None:
        with self._lock:
            for key in keys:
                self._data.pop(key, None)

    def invalidate_prefix(self, prefix: str) -> None:
        with self._lock:
            for key in [k for k in self._data if k.startswith(prefix)]:
                del self._data[key]


class ValkeyCache:
    """کش Valkey/Redis — با fallback خودکار به InMemoryCache در صورت قطع."""

    def __init__(self, url: str = "redis://localhost:6379/0", fallback: CacheBackend | None = None):
        self._fallback = fallback or InMemoryCache()
        self._client = None
        try:
            import redis

            self._client = redis.Redis.from_url(url, socket_connect_timeout=0.5)
            self._client.ping()
        except Exception:  # noqa: BLE001 — Valkey در دسترس نیست → fallback
            self._client = None

    def get(self, key: str) -> Any | None:
        if self._client is None:
            return self._fallback.get(key)
        try:
            raw = self._client.get(key)
            return json.loads(raw) if raw is not None else None
        except Exception:  # noqa: BLE001
            return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        if self._client is None:
            self._fallback.set(key, value, ttl)
            return
        try:
            self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception:  # noqa: BLE001
            self._fallback.set(key, value, ttl)

    def invalidate(self, *keys: str) -> None:
        if self._client is None:
            self._fallback.invalidate(*keys)
            return
        try:
            self._client.delete(*keys)
        except Exception:  # noqa: BLE001
            self._fallback.invalidate(*keys)

    def invalidate_prefix(self, prefix: str) -> None:
        if self._client is None:
            self._fallback.invalidate_prefix(prefix)
            return
        try:
            keys = list(self._client.scan_iter(match=f"{prefix}*"))
            if keys:
                self._client.delete(*keys)
        except Exception:  # noqa: BLE001
            self._fallback.invalidate_prefix(prefix)


_cache: CacheBackend | None = None


def get_cache() -> CacheBackend:
    global _cache
    if _cache is None:
        from app.config import settings

        url = getattr(settings, "valkey_url", "redis://localhost:6379/0")
        _cache = ValkeyCache(url=url)
    return _cache


def reset_cache(cache: CacheBackend | None = None) -> None:
    """برای تست‌ها — جایگزینی/بازنشانی کش سراسری."""
    global _cache
    _cache = cache

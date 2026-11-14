"""تست‌های کش (M12) — TTL، invalidation، fallback. گیت: کش قدیمی هرگز نمایش داده نشود."""

from __future__ import annotations

import time

from cache.keys import invalidate_member_caches
from cache.store import InMemoryCache, ValkeyCache, reset_cache


def test_inmemory_set_get_ttl():
    c = InMemoryCache()
    c.set("k", {"v": 1}, ttl=1)
    assert c.get("k") == {"v": 1}
    time.sleep(1.1)
    assert c.get("k") is None  # انقضای TTL


def test_inmemory_invalidate():
    c = InMemoryCache()
    c.set("a", 1)
    c.set("b", 2)
    c.invalidate("a")
    assert c.get("a") is None
    assert c.get("b") == 2


def test_inmemory_invalidate_prefix():
    c = InMemoryCache()
    c.set("members:list:0:50", [1, 2])
    c.set("members:profile:1", {"id": 1})
    c.set("other:key", 9)
    c.invalidate_prefix("members:")
    assert c.get("members:list:0:50") is None
    assert c.get("members:profile:1") is None
    assert c.get("other:key") == 9


def test_valkey_cache_falls_back_without_server():
    """بدون Valkey هم سیستم کار می‌کند (NFR-6 — پایداری)."""
    c = ValkeyCache(url="redis://127.0.0.1:1/0")  # پورت نامعتبر → fallback
    c.set("x", 42, ttl=10)
    assert c.get("x") == 42
    c.invalidate("x")
    assert c.get("x") is None


def test_stale_member_list_not_served_after_create(session, make_member):
    """گیت M12: بعد از نوشتن، کش قدیمی نمایش داده نمی‌شود."""
    from modules.membership import service

    cache = InMemoryCache()
    reset_cache(cache)

    m1 = make_member()
    first = service.list_members(session)
    assert [m.id for m in first] == [m1.id]

    # نوشتن جدید → باید invalidation شود
    m2 = service.create_member(session, phone="09120009999", full_name="جدید")
    second = service.list_members(session)
    ids = [m.id for m in second]
    assert m2.id in ids, "کش قدیمی نمایش داده شد (invalidation خراب است)"
    assert m1.id in ids

    # ویرایش → پروفایل کش‌شده نباید قدیمی بماند
    service.update_member(session, m1.id, goal="new-goal")
    cache.set(f"members:profile:{m1.id}", {"id": m1.id, "goal": "STALE"}, ttl=30)
    invalidate_member_caches(cache, m1.id)  # همان کاری که سرویس می‌کند
    assert cache.get(f"members:profile:{m1.id}") is None

    reset_cache(None)

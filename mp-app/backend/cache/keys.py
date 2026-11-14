"""کلیدهای کش — قرارداد ثابت برای invalidation قابل اتکا."""

from __future__ import annotations


def members_list_key(offset: int, limit: int) -> str:
    return f"members:list:{offset}:{limit}"


def member_profile_key(member_id: int) -> str:
    return f"members:profile:{member_id}"


MEMBERS_PREFIX = "members:"


def invalidate_member_caches(cache, member_id: int | None = None) -> None:
    """باطل‌سازی کش اعضا بعد از هر نوشتن (قانون لایهٔ ۱۲)."""
    cache.invalidate_prefix(MEMBERS_PREFIX)
    if member_id is not None:
        cache.invalidate(member_profile_key(member_id))

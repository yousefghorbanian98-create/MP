"""فاز ۸ (QF-21) — inbox: تحویل at-least-once ← اثر «یک‌بار».

outbox تضمین می‌کند رویداد گم نشود؛ اما هر dispatch می‌تواند تکراری باشد.
این لایه همان تکرار را بی‌اثر می‌کند: اثر handler فقط وقتی ثبت می‌شود که
پیام با `(topic, dedup_key)` تازه باشد، و **در همان تراکنش** با خودِ پیام.

# قرارداد

| مورد | قاعده |
|---|---|
| تحویل دوباره | handler یک‌بار اجرا می‌شود؛ بار دوم `duplicate` |
| خطای handler | ردیف پیام باقی نمی‌ماند (rollback) تا retry ممکن بماند |
| بدون dedup_key | هر تحویل مستقل است (اثر تکراری ممکن؛ مسئولیت caller) |
| commit اتمیک | پیام و اثر handler با هم commit/rollback می‌شوند |

# آنچه تست نمی‌کند
تحویل واقعی از یک broker بیرونی (`BLOCKED`).
"""

from __future__ import annotations

import pytest

from db.models import InboxMessage
from modules.outbox.inbox import consume_once, inbox_count


def test_same_message_is_consumed_once(session) -> None:
    effects: list[str] = []

    first = consume_once(
        session, topic="payment.approved", dedup_key="evt-1", handler=lambda: effects.append("a")
    )
    second = consume_once(
        session, topic="payment.approved", dedup_key="evt-1", handler=lambda: effects.append("b")
    )

    assert first["status"] == "consumed"
    assert second["status"] == "duplicate"
    assert effects == ["a"]
    assert inbox_count(session) == 1


def test_different_keys_are_independent(session) -> None:
    effects: list[int] = []
    consume_once(session, topic="t", dedup_key="k1", handler=lambda: effects.append(1))
    consume_once(session, topic="t", dedup_key="k2", handler=lambda: effects.append(2))
    assert effects == [1, 2]
    assert inbox_count(session) == 2


def test_handler_failure_rolls_the_message_back(session) -> None:
    def boom() -> None:
        raise RuntimeError("consumer crashed")

    with pytest.raises(RuntimeError):
        consume_once(session, topic="t", dedup_key="k3", handler=boom)
    session.rollback()
    assert inbox_count(session) == 0
    # retry مجاز است و یک‌بار اثر می‌گذارد.
    ok = consume_once(session, topic="t", dedup_key="k3", handler=lambda: None)
    assert ok["status"] == "consumed"


def test_missing_dedup_key_is_rejected_loudly(session) -> None:
    from app.errors import ApiError

    with pytest.raises(ApiError):
        consume_once(session, topic="t", dedup_key="", handler=lambda: None)
    assert session.query(InboxMessage).count() == 0

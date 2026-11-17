"""G7 — حل تعارض LWW.

سه تله‌ای که این تست‌ها می‌گیرند:
۱. ساعت دروغین کلاینت (reject_clock_skew)
۲. گم‌شدن داده در تساوی timestamp (tie-break قطعی)
۳. گزارش‌نشدن تعارض (همیشه action صریح)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from engine.sync_lww import (
    LWW_VERSION,
    MAX_CLOCK_SKEW,
    Versioned,
    resolve,
    resolve_batch,
)

NOW = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)


def v(key: str, minutes_ago: float, device: str = "devA", entity: str = "set_feedback"):
    return Versioned(entity, key, NOW - timedelta(minutes=minutes_ago), device)


class TestNoServerRecord:
    def test_client_wins_when_server_is_empty(self) -> None:
        r = resolve(None, v("1", 5), server_now=NOW)
        assert r["action"] == "accept"
        assert r["winner"] == "client"

    def test_reason_is_explicit(self) -> None:
        r = resolve(None, v("1", 0), server_now=NOW)
        assert "وجود نداشت" in r["reason"]


class TestClientNewer:
    def test_newer_client_overwrites(self) -> None:
        r = resolve(v("1", 10), v("1", 5), server_now=NOW)
        assert r["action"] == "accept"
        assert r["winner"] == "client"
        assert r["client_payload"] is not None or r["client_payload"] is None  # field exists


class TestServerNewer:
    def test_stale_client_is_rejected_not_merged(self) -> None:
        r = resolve(v("1", 5), v("1", 10), server_now=NOW)
        assert r["action"] == "reject_stale"
        assert r["winner"] == "server"

    def test_rejection_is_visible_to_the_user(self) -> None:
        r = resolve(v("1", 5), v("1", 10), server_now=NOW)
        assert "جدیدتر" in r["reason"]
        assert r["delta_seconds"] == -300


class TestClockSkew:
    def test_future_client_clock_is_rejected(self) -> None:
        future = Versioned("set_feedback", "1", NOW + timedelta(hours=2), "devX")
        r = resolve(None, future, server_now=NOW)
        assert r["action"] == "reject_clock_skew"

    def test_small_skew_is_tolerated(self) -> None:
        slight = Versioned("set_feedback", "1", NOW + MAX_CLOCK_SKEW - timedelta(seconds=1), "devX")
        r = resolve(None, slight, server_now=NOW)
        assert r["action"] == "accept"

    def test_skew_boundary_is_exact(self) -> None:
        at_limit = Versioned("set_feedback", "1", NOW + MAX_CLOCK_SKEW, "devX")
        r = resolve(None, at_limit, server_now=NOW)
        assert r["action"] == "accept"  # دقیقاً روی مرز، هنوز مجاز

    def test_skew_message_states_the_magnitude(self) -> None:
        future = Versioned("set_feedback", "1", NOW + timedelta(hours=1), "devX")
        r = resolve(None, future, server_now=NOW)
        assert "۳۶۰۰" in r["reason"] or "3600" in r["reason"]


class TestTieBreak:
    def test_identical_timestamp_from_the_same_device_is_a_retry(self) -> None:
        """تلاش مجدد شبکه نباید «اعمال دوباره» شمرده شود."""
        a = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "deviceA")
        b = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "deviceA")
        r = resolve(a, b, server_now=NOW)
        assert r["action"] == "conflict_resolved"
        assert r["winner"] == "server"
        assert "بی‌اثر" in r["reason"]

    def test_identical_timestamp_from_different_devices_uses_tie_break(self) -> None:
        a = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "deviceA")
        b = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "deviceB")
        r = resolve(a, b, server_now=NOW)
        assert r["action"] == "conflict_resolved"
        assert r["winner"] == "client"  # deviceB > deviceA

    def test_tie_break_is_stable_across_calls(self) -> None:
        a = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "deviceA")
        b = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "deviceC")
        first = resolve(a, b, server_now=NOW)["winner"]
        second = resolve(a, b, server_now=NOW)["winner"]
        assert first == second, "tie-break نباید تصادفی باشد"

    def test_lower_device_id_loses(self) -> None:
        a = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "zzz")
        b = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "aaa")
        assert resolve(a, b, server_now=NOW)["winner"] == "server"

    def test_empty_server_device_never_wins_by_accident(self) -> None:
        """رگرسیون: مقایسه با رشتهٔ خالی یک retry را «جدید» می‌کرد."""
        a = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "")
        b = Versioned("set_feedback", "1", NOW - timedelta(minutes=5), "phone-1")
        r = resolve(a, b, server_now=NOW)
        assert r["winner"] == "client"  # بر اساس ترتیب الفبایی، نه خالی بودن

    def test_naive_timestamps_do_not_crash(self) -> None:
        a = Versioned("set_feedback", "1", (NOW - timedelta(minutes=5)).replace(tzinfo=None), "d1")
        b = Versioned("set_feedback", "1", NOW - timedelta(minutes=1), "d2")
        assert resolve(a, b, server_now=NOW)["action"] == "accept"


class TestBatch:
    def test_counts_are_consistent(self) -> None:
        server = {("set_feedback", "1"): v("1", 5), ("set_feedback", "2"): v("2", 1)}
        client = [v("1", 1), v("2", 10), v("3", 0)]
        r = resolve_batch(server, client, server_now=NOW)
        c = r["counts"]
        assert c["received"] == 3
        assert c["applied"] == 2  # 1 جدیدتر، 3 جدید
        assert c["rejected"] == 1  # 2 قدیمی‌تر
        assert c["applied"] + c["rejected"] == c["received"]

    def test_every_item_has_an_explicit_action(self) -> None:
        r = resolve_batch({}, [v("1", 0), v("2", 0)], server_now=NOW)
        assert all(item["action"] for item in r["results"])

    def test_empty_batch(self) -> None:
        r = resolve_batch({}, [], server_now=NOW)
        assert r["counts"]["received"] == 0
        assert r["results"] == []

    def test_entities_do_not_collide(self) -> None:
        """کلید یکتا (entity, key) است، نه فقط key."""
        server = {("other_entity", "1"): v("1", 1, entity="other_entity")}
        r = resolve_batch(server, [v("1", 5)], server_now=NOW)
        assert r["results"][0]["action"] == "accept"


class TestVersioning:
    def test_rule_version_is_reported(self) -> None:
        assert resolve(None, v("1", 0), server_now=NOW)["rule_version"] == LWW_VERSION

    @pytest.mark.parametrize("minutes", [0, 5, 60, 1440])
    def test_any_age_is_handled(self, minutes: float) -> None:
        r = resolve(None, v("1", minutes), server_now=NOW + timedelta(days=1))
        assert r["action"] in ("accept", "reject_clock_skew")

"""WP 3.6 (F‑28، الحاقیهٔ A1) — «امروز» دامنهٔ سلامت باید منطقهٔ فروشگاه باشد.

قبل از اصلاح: `date.today()` در axis_assessment و nutrition به ساعت کانتینر (UTC)
وابسته بود؛ ۰۰:۰۰–۰۳:۳۰ تهران روز اشتباه. بعد: `app.clock.today_in_shop_zone()`؛
ENV TZ در هر دو Dockerfile (لایهٔ دوم، AD‑1).
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

import app.clock as clock
from modules.axis_assessment.service import _member_age_sex

BACKEND = Path(__file__).resolve().parents[2]
# ساعت ۲۱:۰۰ UTC = ۰۰:۳۰ روز بعد در تهران (+۰۳:۳۰)
FROZEN_UTC = datetime(2030, 3, 20, 21, 0, tzinfo=UTC)


@pytest.fixture
def frozen_clock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clock, "_now_utc", lambda: FROZEN_UTC)


def test_today_is_shop_zone_day_near_midnight(frozen_clock) -> None:
    """ساعت ۰۰:۳۰ تهران ⇒ تاریخ همان روز تهران، نه UTC."""
    assert clock.today_in_shop_zone() == date(2030, 3, 21)


def test_axis_age_uses_shop_day(frozen_clock) -> None:
    """تولدِ ۲۱ مارس: با روز تهران سن ۳۰ است؛ با روز UTC ۲۹ می‌شد."""
    member = SimpleNamespace(birth_date=date(2000, 3, 21), gender="male")
    age, _sex = _member_age_sex(member)
    assert age == 30


def test_no_naive_date_today_in_domain_code() -> None:
    """هیچ `date.today()` در modules/app/engine/jobs نماند (گیت A1.3 after-wp36)."""
    hits: list[str] = []
    for root in ("modules", "app", "engine", "jobs"):
        for path in (BACKEND / root).rglob("*.py"):
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if re.search(r"\bdate\.today\(", line):
                    hits.append(f"{path.relative_to(BACKEND)}:{n}")
    assert hits == []


@pytest.mark.parametrize("dockerfile", ["Dockerfile", "../infra/Dockerfile.backend"])
def test_container_timezone_is_shop_zone(dockerfile: str) -> None:
    """لایهٔ دوم: ENV TZ=Asia/Tehran در ایمیج‌ها."""
    text = (BACKEND / dockerfile).read_text(encoding="utf-8")
    assert re.search(r"^ENV .*\bTZ=Asia/Tehran\b", text, re.M), dockerfile

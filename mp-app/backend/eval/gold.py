"""استاندارد طلایی مستقل از موتور — بازه‌های مبانی ورزشی (ACSM-سبک).

این بازه‌ها «قضاوت مربی» هستند و عمداً جدا از `engine.workout.RULES` نوشته
می‌شوند تا توافق موتور با آن‌ها اندازه‌گیری شود، نه اینکه از آن‌ها تقلید کند.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GoldRange:
    sets: tuple[int, int]
    reps: frozenset[str]  # مقادیر مجاز رشتهٔ تکرار
    load_pct: tuple[int, int]
    rest: tuple[int, int]


# نمونهٔ تکرارهای مجاز هر هدف (رشته‌های بازه یا تک رقمی)
_REPS_HYP = frozenset({"6-12", "8-12", "10-12", "8-10", "6-10", "12", "10", "12-15"})
_REPS_STR = frozenset({"3", "3-5", "5", "5-8", "1-5", "2-5"})
_REPS_WL = frozenset({"10-15", "12-15", "12-20", "15", "12", "15-20"})
_REPS_FIT = frozenset({"10-12", "12", "12-15", "15", "10-15"})

GOLD: dict[tuple[str, str], GoldRange] = {
    ("hypertrophy", "beginner"): GoldRange((2, 4), _REPS_HYP, (55, 72), (60, 120)),
    ("hypertrophy", "intermediate"): GoldRange((3, 5), _REPS_HYP, (60, 80), (60, 150)),
    ("hypertrophy", "advanced"): GoldRange((3, 5), _REPS_HYP, (65, 85), (60, 180)),
    ("strength", "beginner"): GoldRange((3, 5), _REPS_STR, (65, 80), (90, 240)),
    ("strength", "intermediate"): GoldRange((3, 5), _REPS_STR, (70, 88), (120, 300)),
    ("strength", "advanced"): GoldRange((3, 5), _REPS_STR, (75, 95), (120, 300)),
    ("weight_loss", "beginner"): GoldRange((2, 4), _REPS_WL, (45, 65), (30, 90)),
    ("weight_loss", "intermediate"): GoldRange((2, 4), _REPS_WL, (50, 72), (30, 90)),
    ("weight_loss", "advanced"): GoldRange((2, 4), _REPS_WL, (55, 78), (30, 120)),
    ("fitness", "beginner"): GoldRange((2, 3), _REPS_FIT, (40, 62), (30, 90)),
    ("fitness", "intermediate"): GoldRange((2, 4), _REPS_FIT, (45, 68), (30, 120)),
    ("fitness", "advanced"): GoldRange((2, 4), _REPS_FIT, (50, 72), (30, 120)),
}

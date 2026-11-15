"""ماتریس سناریوهای ارزیابی — پوشش اهداف/سطوح/روزها/محدودیت‌ها/مسیرهای جمعیتی."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Scenario:
    sid: str
    goal: str
    level: str
    days: int
    weeks: int = 8
    constraints: tuple[str, ...] = field(default_factory=tuple)
    population: str = "adult"
    expect: str = "generate"  # generate | block


def _build() -> list[Scenario]:
    out: list[Scenario] = []
    # (۱) پوشش کامل هدف × سطح با ۳ روز (۱۲ سناریو)
    for goal in ("hypertrophy", "strength", "weight_loss", "fitness"):
        for level in ("beginner", "intermediate", "advanced"):
            out.append(Scenario(f"{goal}-{level}-3d", goal, level, 3))
    # (۲) پوشش تعداد روز (۴/۵/۶) روی هدف/سطح میانی
    for days in (4, 5, 6):
        out.append(
            Scenario(f"hypertrophy-intermediate-{days}d", "hypertrophy", "intermediate", days)
        )
    # (۳) محدودیت‌های حرکتی — هیچ حرکت ممنوعه‌ای نباید بماند
    for c in ("knee", "shoulder", "lower_back", "wrist"):
        out.append(Scenario(f"constraint-{c}", "hypertrophy", "intermediate", 3, constraints=(c,)))
    # (۴) گیت جمعیتی — مسیرهای مجاز باید بسازند، بقیه باید متوقف شوند
    out.append(Scenario("population-senior", "fitness", "beginner", 3, population="senior_healthy"))
    for pid in (
        "youth",
        "pregnancy_postpartum",
        "disability",
        "disease",
        "return_from_injury",
        "elite",
    ):
        out.append(
            Scenario(
                f"population-{pid}", "hypertrophy", "beginner", 3, population=pid, expect="block"
            )
        )
    # (۵) جمعیت ناشناخته باید رد شود
    out.append(
        Scenario(
            "population-unknown", "fitness", "beginner", 3, population="martian", expect="block"
        )
    )
    return out


SCENARIOS: list[Scenario] = _build()

# حرکات ممنوعهٔ واقعی به‌ازای هر محدودیت (قضاوت مربی — مستقل از CONSTRAINT_SWAPS)
FORBIDDEN_MOVES: dict[str, frozenset[str]] = {
    "knee": frozenset({"back_squat", "lunge"}),
    "shoulder": frozenset({"overhead_press", "bench_press"}),
    "lower_back": frozenset({"deadlift", "back_squat"}),
    "wrist": frozenset({"bench_press", "barbell_row"}),
}

"""هستهٔ اندازه‌گیری — اجرای سناریوها و محاسبهٔ شش معیار."""

from __future__ import annotations

from typing import Any

from app.errors import ApiError
from engine.workout import (
    CONSTRAINT_SWAPS,
    DAY_MOVES,
    ENGINE_VERSION,
    LIBRARY,
    generate_program,
)
from eval.gold import GOLD
from eval.scenarios import FORBIDDEN_MOVES, SCENARIOS, Scenario
from modules.population.gates import assert_generation_allowed


def _check_library_integrity() -> list[str]:
    """هر کلید/مقصد باید در کتابخانه وجود داشته باشد — گیرندهٔ نشت تعویض."""
    problems: list[str] = []
    for day_moves in DAY_MOVES.values():
        for key in day_moves:
            if key not in LIBRARY:
                problems.append(f"DAY_MOVES: «{key}» در LIBRARY نیست")
    for injury, swaps in CONSTRAINT_SWAPS.items():
        for src, dst in swaps.items():
            if src not in LIBRARY:
                problems.append(f"CONSTRAINT_SWAPS[{injury}]: مبدأ «{src}» در LIBRARY نیست")
            if dst not in LIBRARY:
                problems.append(
                    f"CONSTRAINT_SWAPS[{injury}]: مقصد «{dst}» در LIBRARY نیست ← تعویض بی‌اثر/خطرناک"
                )
    return problems


def _check_structural(sc: Scenario, plan) -> list[str]:
    problems: list[str] = []
    if len(plan.weeks) != sc.weeks:
        problems.append(f"{sc.sid}: تعداد هفته {len(plan.weeks)} ≠ {sc.weeks}")
    for week in plan.weeks:
        days_seen = {e.day for e in week.exercises}
        if days_seen != set(range(1, sc.days + 1)):
            problems.append(
                f"{sc.sid}/هفته{week.week_number}: روزها {sorted(days_seen)} ≠ ۱..{sc.days}"
            )
        for e in week.exercises:
            if not (30 <= e.load_pct <= 95):
                problems.append(f"{sc.sid}: لود {e.load_pct} خارج از بازهٔ مجاز")
    # پیشرفت یکنواخت لود (مونوتون)
    loads = [max(e.load_pct for e in w.exercises) for w in plan.weeks]
    if any(loads[i] > loads[i + 1] for i in range(len(loads) - 1)):
        problems.append(f"{sc.sid}: لود هفتگی نزولی شد {loads}")
    return problems


def _check_gold(sc: Scenario, plan) -> tuple[int, int]:
    """(سازگار، کل) — توافق قضاوت مربی با بازه‌های طلایی."""
    gold = GOLD[(sc.goal, sc.level)]
    ok = total = 0
    for week in plan.weeks:
        for e in week.exercises:
            total += 1
            lo, hi = gold.sets
            load_lo, load_hi = gold.load_pct
            rest_lo, rest_hi = gold.rest
            if (
                lo <= e.sets <= hi
                and e.reps in gold.reps
                and load_lo <= e.load_pct <= load_hi
                and rest_lo <= e.rest_seconds <= rest_hi
            ):
                ok += 1
    return ok, total


def _check_constraints(sc: Scenario, plan) -> list[str]:
    problems: list[str] = []
    for c in sc.constraints:
        forbidden = FORBIDDEN_MOVES.get(c, frozenset())
        for week in plan.weeks:
            for e in week.exercises:
                for key, move in LIBRARY.items():
                    if move["name"] == e.name and key in forbidden:
                        problems.append(
                            f"{sc.sid}: حرکت ممنوعه «{e.name}» برای محدودیت {c} باقی ماند"
                        )
    return problems


def run_all() -> dict[str, Any]:
    """اجرا + معیارها — خروجی JSON-پسند."""
    library_problems = _check_library_integrity()
    population_violations: list[str] = []
    constraint_violations: list[str] = []
    structural_problems: list[str] = []
    gold_ok = gold_total = 0
    determinism_pass = True
    generated = blocked = 0

    for sc in SCENARIOS:
        # گیت جمعیتی
        try:
            assert_generation_allowed(sc.population)
            gate_allows = True
        except ApiError:
            gate_allows = False
        if sc.expect == "block" and gate_allows:
            population_violations.append(
                f"{sc.sid}: گیت باید می‌بست ولی باز گذاشت ← تولید خودکار غیرمجاز!"
            )
        if sc.expect == "generate" and not gate_allows:
            population_violations.append(f"{sc.sid}: گیت نباید می‌بست ولی بست")

        if sc.expect == "block":
            blocked += 1
            continue
        generated += 1
        plan = generate_program(sc.goal, sc.level, sc.days, sc.weeks, list(sc.constraints))
        structural_problems += _check_structural(sc, plan)
        constraint_violations += _check_constraints(sc, plan)
        ok, total = _check_gold(sc, plan)
        gold_ok += ok
        gold_total += total
        # قطعیت: همان ورودی ← همان خروجی
        plan2 = generate_program(sc.goal, sc.level, sc.days, sc.weeks, list(sc.constraints))
        if plan.to_engine_output() != plan2.to_engine_output():
            determinism_pass = False

    total_slots = gold_total
    return {
        "engine_version": ENGINE_VERSION,
        "scenarios_total": len(SCENARIOS),
        "scenarios_generated": generated,
        "scenarios_blocked": blocked,
        "safety_population_violations": population_violations,
        "safety_constraint_violations": constraint_violations,
        "library_integrity_problems": library_problems,
        "structural_problems": structural_problems,
        "determinism_pass": determinism_pass,
        "gold_agreement": {
            "matching_slots": gold_ok,
            "total_slots": total_slots,
            "pct": round(100 * gold_ok / total_slots, 1) if total_slots else 0.0,
        },
    }

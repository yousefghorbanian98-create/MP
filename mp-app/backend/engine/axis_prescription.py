"""تجویز محور-آگاه حرکات — نسخهٔ `axis-prescription-1.0` (M38-c1).

قاعده‌ها (دترمینیستیک — بدون LLM در انتخاب/اعداد):
    direct   ← حرکت اختصاصی از نردبان محور (پایین‌ترین سطح مناسب نمره) با ست کامل
    maintain ← حرکت سطح بالاتر با دوز کم (نگهداری)
    covered  ← بدون کار اختصاصی؛ اگر حرکت منتخب دیگری پوشش می‌دهد ← فهرست آن؛
               وگرنه یک «حامل چندمحوره» (پوشش این محور + حداقل یک محور دیگر) انتخاب می‌شود
    refer    ← بدون تجویز + دلیل (هرگز «عمومی + هشدار» — D-016)
    unknown  ← بدون تجویز + دلیل (داده ناشناخته است نه صفر)
قانون «یک حرکت، چند محور، یک‌بار بار»: حرکت تکراری فقط یک‌بار شمرده می‌شود (load-attribution-1.0).
بودجهٔ خستگی هفتگی: اگر مجموع ست‌ها بیش از بودجه شود، اول maintain بریده می‌شود، سپس covered — هرگز direct.
"""

from __future__ import annotations

from app.errors import ApiError
from engine.axis_rules import LOAD_RULES_VERSION, attribute_load, tally_weekly_load

PRESCRIPTION_VERSION = "axis-prescription-1.0"

DIRECT_SETS = 3
MAINTAIN_SETS = 2
COVERED_MIN_WEIGHT = 0.3
DIRECT_MIN_WEIGHT = 0.5
DEFAULT_FATIGUE_BUDGET = 14.0


def _covering(movements: list[dict], axis: int, min_weight: float) -> list[dict]:
    return [
        m for m in movements if float(m.get("axis_coverage", {}).get(str(axis), 0.0)) >= min_weight
    ]


def _pick_level(movers: list[dict], prefer_low: bool) -> dict | None:
    if not movers:
        return None
    return sorted(
        movers,
        key=lambda m: (m.get("level", 99) if prefer_low else -m.get("level", 0), m["external_id"]),
    )[0]


def prescribe_axis_work(
    *,
    decisions: dict[int, dict],
    movements: list[dict],
    fatigue_budget: float = DEFAULT_FATIGUE_BUDGET,
) -> dict:
    """برنامهٔ کار هر محور + بار هفتگی (خستگی یک‌بار) + دلیل‌ها."""
    if not decisions:
        raise ApiError("هیچ تصمیم محوری داده نشده", code="missing_decisions")
    if not movements:
        raise ApiError("کاتالوگ حرکات خالی است", code="missing_movements")
    for m in movements:
        if "external_id" not in m or not m.get("axis_coverage"):
            raise ApiError(
                "حرکت بدون external_id یا بردار پوشش — داده ناشناخته است نه صفر",
                code="invalid_movement",
            )

    axis_plans: dict[int, dict] = {}
    selected: dict[str, dict] = {}  # external_id → movement (dedup)
    sets_by_movement: dict[str, float] = {}
    trimmed: list[str] = []

    def _select(mover: dict, sets: float, axis: int, role: str, plan_for_axis: dict) -> None:
        mid = mover["external_id"]
        selected.setdefault(mid, mover)
        # ست‌ها: بیشینهٔ درخواست‌شده (حرکت مشترک ست‌هایش ضرب نمی‌شود — یک‌بار)
        sets_by_movement[mid] = max(sets_by_movement.get(mid, 0.0), sets)
        plan_for_axis["movement_ids"].append(mid)
        plan_for_axis["roles"].append(role)

    def _new_plan(axis: int, d: dict) -> dict:
        return {
            "axis": axis,
            "state": d.get("state"),
            "movement_ids": [],
            "roles": [],
            "sets": 0,
            "reason": d.get("reason", ""),
        }

    # پاس ۱: direct + maintain (تا پوشش‌ها در پاس ۲ دیده شوند)؛ پاس ۲: covered
    pass1 = [a for a in sorted(decisions) if decisions[a].get("state") in ("direct", "maintain")]
    pass2 = [a for a in sorted(decisions) if decisions[a].get("state") == "covered"]
    pass3 = [
        a
        for a in sorted(decisions)
        if decisions[a].get("state") not in ("direct", "maintain", "covered")
    ]

    for axis in pass1 + pass2 + pass3:
        d = decisions[axis]
        state = d.get("state")
        plan_for_axis = _new_plan(axis, d)
        if state == "direct":
            mover = _pick_level(_covering(movements, axis, DIRECT_MIN_WEIGHT), prefer_low=True)
            if mover is None:
                plan_for_axis["reason"] += " — اما حرکت مناسب در کاتالوگ یافت نشد (شکاف محتوا)"
            else:
                _select(mover, DIRECT_SETS, axis, "direct", plan_for_axis)
                plan_for_axis["sets"] = DIRECT_SETS
        elif state == "maintain":
            mover = _pick_level(_covering(movements, axis, COVERED_MIN_WEIGHT), prefer_low=False)
            if mover is not None:
                _select(mover, MAINTAIN_SETS, axis, "maintain", plan_for_axis)
                plan_for_axis["sets"] = MAINTAIN_SETS
        elif state == "covered":
            carriers = [
                m
                for m in selected.values()
                if float(m.get("axis_coverage", {}).get(str(axis), 0.0)) >= COVERED_MIN_WEIGHT
            ]
            if carriers:
                plan_for_axis["movement_ids"] = [m["external_id"] for m in carriers]
                plan_for_axis["roles"] = ["covered_in"] * len(carriers)
                plan_for_axis["reason"] += " — پوشش از حرکات منتخب دیگر"
            else:
                multi = [
                    m
                    for m in _covering(movements, axis, COVERED_MIN_WEIGHT)
                    if sum(1 for w in m["axis_coverage"].values() if float(w) >= COVERED_MIN_WEIGHT)
                    >= 2
                ]
                mover = _pick_level(multi, prefer_low=True)
                if mover is not None:
                    _select(mover, DIRECT_SETS, axis, "carrier", plan_for_axis)
                    plan_for_axis["sets"] = DIRECT_SETS
                    plan_for_axis["reason"] += " — حامل چندمحوره انتخاب شد"
        # refer/unknown: بدون تجویز — دلیل همان reason تصمیم است
        axis_plans[axis] = plan_for_axis

    # بودجهٔ خستگی: اول maintain، سپس carrier — هرگز direct
    entries = [
        attribute_load(movement_id=mid, axis_coverage=selected[mid]["axis_coverage"], sets=sets)
        for mid, sets in sets_by_movement.items()
        if sets > 0
    ]
    total = sum(e["fatigue_units"] for e in entries)
    if total > fatigue_budget:
        # اول maintain، سپس carrier — هرگز direct (قاعدهٔ ثبت‌شده)
        for role_cut in ("maintain", "carrier"):
            for plan in axis_plans.values():
                for mid, role in zip(plan["movement_ids"], plan["roles"], strict=True):
                    if total <= fatigue_budget:
                        break
                    if role == role_cut and sets_by_movement.get(mid, 0) > 0:
                        cut = min(sets_by_movement[mid], total - fatigue_budget)
                        sets_by_movement[mid] -= cut
                        total -= cut
                        trimmed.append(f"{mid}: -{cut} ست (بودجهٔ خستگی — {role_cut})")
        entries = [
            attribute_load(movement_id=mid, axis_coverage=selected[mid]["axis_coverage"], sets=sets)
            for mid, sets in sets_by_movement.items()
            if sets > 0
        ]
    load = (
        tally_weekly_load(entries)
        if entries
        else {
            "total_fatigue": 0.0,
            "axis_totals": {},
            "movements_counted": 0,
            "reason": "هیچ حرکتی تجویز نشد",
            "rule_version": LOAD_RULES_VERSION,
        }
    )
    return {
        "axis_plans": [axis_plans[a] for a in sorted(axis_plans)],
        "selected": [
            {
                **{
                    k: selected[mid][k]
                    for k in ("external_id", "name_fa", "intensity_band", "progression_key")
                    if k in selected[mid]
                },
                "sets": sets_by_movement.get(mid, 0.0),
            }
            for mid in selected
        ],
        "load": load,
        "trimmed": trimmed,
        "rule_version": PRESCRIPTION_VERSION,
        "reason": (
            f"{sum(1 for p in axis_plans.values() if p['movement_ids'])} محور تجویز شد؛ "
            f"{len(selected)} حرکت یکتا ← خستگی جمعاً {load['total_fatigue']} (هر ست یک‌بار)"
        ),
    }

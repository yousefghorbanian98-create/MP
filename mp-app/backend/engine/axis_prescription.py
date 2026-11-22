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


def _new_plan(axis: int, d: dict) -> dict:
    return {
        "axis": axis,
        "state": d.get("state"),
        "movement_ids": [],
        "roles": [],
        "sets": 0,
        "reason": d.get("reason", ""),
    }


class _Prescription:
    """وضعیت یک اجرای تجویز. مراحل همان ترتیب و همان قواعد نسخهٔ HEAD را دارند (B5 / WP 4.1)."""

    def __init__(self, movements: list[dict]) -> None:
        self.movements = movements
        self.axis_plans: dict[int, dict] = {}
        self.selected: dict[str, dict] = {}  # external_id → movement (dedup)
        self.sets_by_movement: dict[str, float] = {}
        self.trimmed: list[str] = []

    def select(self, mover: dict, sets: float, axis: int, role: str, plan: dict) -> None:
        mid = mover["external_id"]
        self.selected.setdefault(mid, mover)
        # ست‌ها: بیشینهٔ درخواست‌شده (حرکت مشترک ست‌هایش ضرب نمی‌شود — یک‌بار)
        self.sets_by_movement[mid] = max(self.sets_by_movement.get(mid, 0.0), sets)
        plan["movement_ids"].append(mid)
        plan["roles"].append(role)

    def plan_direct(self, axis: int, plan: dict) -> None:
        mover = _pick_level(_covering(self.movements, axis, DIRECT_MIN_WEIGHT), prefer_low=True)
        if mover is None:
            plan["reason"] += " — اما حرکت مناسب در کاتالوگ یافت نشد (شکاف محتوا)"
            return
        self.select(mover, DIRECT_SETS, axis, "direct", plan)
        plan["sets"] = DIRECT_SETS

    def plan_maintain(self, axis: int, plan: dict) -> None:
        mover = _pick_level(_covering(self.movements, axis, COVERED_MIN_WEIGHT), prefer_low=False)
        if mover is None:
            return
        self.select(mover, MAINTAIN_SETS, axis, "maintain", plan)
        plan["sets"] = MAINTAIN_SETS

    def plan_covered(self, axis: int, plan: dict) -> None:
        carriers = [
            m
            for m in self.selected.values()
            if float(m.get("axis_coverage", {}).get(str(axis), 0.0)) >= COVERED_MIN_WEIGHT
        ]
        if carriers:
            plan["movement_ids"] = [m["external_id"] for m in carriers]
            plan["roles"] = ["covered_in"] * len(carriers)
            plan["reason"] += " — پوشش از حرکات منتخب دیگر"
            return
        self.plan_carrier(axis, plan)

    def plan_carrier(self, axis: int, plan: dict) -> None:
        multi = [
            m
            for m in _covering(self.movements, axis, COVERED_MIN_WEIGHT)
            if sum(1 for w in m["axis_coverage"].values() if float(w) >= COVERED_MIN_WEIGHT) >= 2
        ]
        mover = _pick_level(multi, prefer_low=True)
        if mover is None:
            return
        self.select(mover, DIRECT_SETS, axis, "carrier", plan)
        plan["sets"] = DIRECT_SETS
        plan["reason"] += " — حامل چندمحوره انتخاب شد"

    def plan_all(self, decisions: dict[int, dict]) -> None:
        # پاس ۱: direct + maintain (تا پوشش‌ها در پاس ۲ دیده شوند)؛ پاس ۲: covered؛ پاس ۳: بقیه
        pass1 = [
            a for a in sorted(decisions) if decisions[a].get("state") in ("direct", "maintain")
        ]
        pass2 = [a for a in sorted(decisions) if decisions[a].get("state") == "covered"]
        pass3 = [
            a
            for a in sorted(decisions)
            if decisions[a].get("state") not in ("direct", "maintain", "covered")
        ]
        for axis in pass1 + pass2 + pass3:
            d = decisions[axis]
            state = d.get("state")
            plan = _new_plan(axis, d)
            if state == "direct":
                self.plan_direct(axis, plan)
            elif state == "maintain":
                self.plan_maintain(axis, plan)
            elif state == "covered":
                self.plan_covered(axis, plan)
            # refer/unknown: بدون تجویز — دلیل همان reason تصمیم است
            self.axis_plans[axis] = plan

    def entries(self) -> list[dict]:
        return [
            attribute_load(
                movement_id=mid,
                axis_coverage=self.selected[mid]["axis_coverage"],
                sets=sets,
            )
            for mid, sets in self.sets_by_movement.items()
            if sets > 0
        ]

    def trim_to_budget(self, fatigue_budget: float) -> list[dict]:
        """بودجهٔ خستگی: اول maintain، سپس carrier — هرگز direct (قاعدهٔ ثبت‌شده)."""
        entries = self.entries()
        total = sum(e["fatigue_units"] for e in entries)
        if total > fatigue_budget:
            for role_cut in ("maintain", "carrier"):
                total = self._trim_role(role_cut, total, fatigue_budget)
            entries = self.entries()
        return entries

    def _trim_role(self, role_cut: str, total: float, fatigue_budget: float) -> float:
        for plan in self.axis_plans.values():
            for mid, role in zip(plan["movement_ids"], plan["roles"], strict=True):
                if total <= fatigue_budget:
                    break
                if role == role_cut and self.sets_by_movement.get(mid, 0) > 0:
                    cut = min(self.sets_by_movement[mid], total - fatigue_budget)
                    self.sets_by_movement[mid] -= cut
                    total -= cut
                    self.trimmed.append(f"{mid}: -{cut} ست (بودجهٔ خستگی — {role_cut})")
        return total


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

    state = _Prescription(movements)
    state.plan_all(decisions)
    entries = state.trim_to_budget(fatigue_budget)
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
    axis_plans = state.axis_plans
    selected = state.selected
    sets_by_movement = state.sets_by_movement
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
        "trimmed": state.trimmed,
        "rule_version": PRESCRIPTION_VERSION,
        "reason": (
            f"{sum(1 for p in axis_plans.values() if p['movement_ids'])} محور تجویز شد؛ "
            f"{len(selected)} حرکت یکتا ← خستگی جمعاً {load['total_fatigue']} (هر ست یک‌بار)"
        ),
    }

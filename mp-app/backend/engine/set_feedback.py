"""بازخورد ست‌به‌ست (G1) — نسخهٔ `set-feedback-1.0` (M38-c2).

هر ست با RIR/درد عضلانی ثبت می‌شود ← پیشنهاد جلسهٔ بعد (وزن/حجم) با دلیل.
هیچ عددی از LLM نمی‌آید (E04) — وزن از autoreg-1.0 (قانون ۲ برای ۲)، حجم از قواعد درد.
"""

from __future__ import annotations

from app.errors import ApiError
from engine.autoreg import suggest_next_weight

SET_FEEDBACK_VERSION = "set-feedback-1.0"

SORENESS_DELOAD = 7  # درد شدید ← کاهش حجم
SORENESS_OK = 3  # درد خفیف/بدون درد ← حجم عادی


def _rpe_from_rir(rir: float | None) -> float | None:
    if rir is None:
        return None
    return max(1.0, min(10.0, 10.0 - float(rir)))


def process_set_feedback(*, entries: list[dict]) -> dict:
    """پردازش ست‌های ثبت‌شده ← پیشنهاد ست/جلسهٔ بعد برای هر حرکت.

    entry: {movement_id, weight, target_reps, reps_done, rir?: float, soreness?: 0..10}
    """
    if not entries:
        raise ApiError("هیچ ستی ثبت نشده — داده ناشناخته است نه صفر", code="missing_entries")

    per_movement: dict[str, list[dict]] = {}
    for entry in entries:
        mid = entry.get("movement_id")
        if not mid:
            raise ApiError("movement_id الزامی است", code="invalid_entry")
        soreness = entry.get("soreness")
        if soreness is not None and not 0 <= soreness <= 10:
            raise ApiError("درد باید بین ۰ و ۱۰ باشد", code="invalid_soreness")
        per_movement.setdefault(mid, []).append(entry)

    suggestions = []
    for mid, sets in sorted(per_movement.items()):
        last = sets[-1]
        last_weight = float(last.get("weight", 0) or 0)
        if last_weight <= 0:
            weight_rule = {
                "next_weight": 0.0,
                "action": "keep_bodyweight",
                "reason": "حرکت با وزن بدن — پیشرفت از طریق تکرار/سطح نردبان",
            }
        else:
            weight_rule = suggest_next_weight(
                last_weight=last_weight,
                reps_done=int(last.get("reps_done", 0)),
                target_reps=int(last.get("target_reps", 0)),
                rpe=_rpe_from_rir(last.get("rir")),
            )
        max_soreness = max((s.get("soreness") or 0) for s in sets)
        # M48-c1 — «حجم جلسه» یعنی تعداد ست‌هایی که عضو *انجام داد*، نه تعداد
        # ردیف‌های گزارش. اگر عضو فقط ۱ ست گزارش کند، len(sets)=1 و کاهش
        # یک‌ستِ آن برنامهٔ ۳ ستی را به ۱ ست می‌رساند — یک باگ منطقی.
        # کفِ منطقی: اگر حرکتی گزارش شده، حداقل همان تعداد ست انجام شده است.
        prescribed_sets = max(
            (int(s.get("sets_done") or 0) for s in sets),
            default=0,
        )
        reported_sets = len(sets)
        effective_sets = max(prescribed_sets, reported_sets)

        if max_soreness >= SORENESS_DELOAD:
            volume_action = "deload"
            # `next_sets` فقط در حالت keep معنا دارد؛ در deload، ست‌ها از
            # روی خودِ برنامه یک واحد کم می‌شوند (engine.feedback_apply).
            next_sets = None
            volume_reason = (
                f"درد عضلانی {max_soreness}/۱۰ ≥ {SORENESS_DELOAD} ← کاهش یک ست جلسهٔ بعد (بازیابی)"
            )
        else:
            volume_action = "keep"
            next_sets = effective_sets
            volume_reason = f"درد عضلانی {max_soreness}/۱۰ در محدودهٔ قابل قبول ← حجم حفظ می‌شود"
        suggestions.append(
            {
                "movement_id": mid,
                "next_weight": weight_rule["next_weight"],
                "weight_action": weight_rule["action"],
                "next_sets": next_sets,
                "volume_action": volume_action,
                "reason": f"{weight_rule['reason']}؛ {volume_reason}",
                "rule_version": SET_FEEDBACK_VERSION,
            }
        )
    return {
        "suggestions": suggestions,
        "reason": f"{len(entries)} ست از {len(per_movement)} حرکت پردازش شد (G1 — بدون عدد از LLM)",
        "rule_version": SET_FEEDBACK_VERSION,
    }

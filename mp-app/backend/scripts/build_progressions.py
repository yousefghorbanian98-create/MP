"""ساخت نردبان‌های پیشرفت (M34-c1) — پیوند مراحل به ردیف‌های واقعی catalog.

قاعده: هیچ پله‌ای بدون ردیف واقعی catalog_exercises ساخته نمی‌شود — اگر نامی در
کاتالوگ نباشد، اجرا با خطای صریح متوقف می‌شود («داده ← قاعده ← شاهد ← تصمیم»).

کاربرد:
    python scripts/build_progressions.py --check   # فقط راستی‌آزمایی نام‌ها در برابر فایل منبع
    python scripts/build_progressions.py           # seed در DB (idempotent)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.base import get_session_factory  # noqa: E402
from db.models.content import CatalogExercise, ProgressionLadder, ProgressionStep  # noqa: E402
from scripts.import_exercise_catalog import DEFAULT_DATA  # noqa: E402


@dataclass(frozen=True)
class Step:
    catalog_name: str
    name_fa: str
    note: str = ""


@dataclass(frozen=True)
class Ladder:
    key: str
    name_fa: str
    axis_focus: dict
    note: str
    steps: tuple[Step, ...]


LADDERS: tuple[Ladder, ...] = (
    Ladder(
        "pushup",
        "شنای سوئدی",
        {"3": 0.8, "5": 0.5, "7": 0.4},
        "نردبان الگوی فشاری بالاتنه",
        (
            Step("Incline Push-Up", "شنای سوئدی شیب‌دار", "سطح ۱ — دست بالاتر"),
            Step("Pushups", "شنای سوئدی استاندارد", "سطح ۲"),
            Step("Push-Ups With Feet Elevated", "شنای سوئدی پاها بالاتر", "سطح ۳"),
        ),
    ),
    Ladder(
        "squat",
        "اسکوات",
        {"3": 0.9, "9": 0.6, "2": 0.3},
        "نردبان الگوی اسکوات",
        (
            Step("Chair Squat", "اسکوات روی صندلی", "سطح ۱"),
            Step("Bodyweight Squat", "اسکوات با وزن بدن", "سطح ۲"),
            Step("Dumbbell Squat", "اسکوات دمبل", "سطح ۳"),
            Step("Barbell Squat", "اسکوات هالتر", "سطح ۴"),
            Step("Front Squat (Clean Grip)", "اسکوات فرانت", "سطح ۵"),
        ),
    ),
    Ladder(
        "pullup",
        "بارفیکس",
        {"3": 0.8, "10": 0.5, "5": 0.4},
        "نردبان الگوی کششی عمودی",
        (
            Step("Band Assisted Pull-Up", "بارفیکس با کش کمکی", "سطح ۱"),
            Step("Pullups", "بارفیکس استاندارد", "سطح ۲"),
            Step("Chin-Up", "چین‌آپ", "سطح ۳"),
            Step("V-Bar Pullup", "بارفیکس وی‌بار", "سطح ۴"),
            Step("Wide-Grip Rear Pull-Up", "بارفیکس دست‌باز پشت", "سطح ۵"),
        ),
    ),
    Ladder(
        "plank",
        "پلانک",
        {"7": 0.8, "5": 0.5},
        "نردبان پایداری مرکز ایزومتریک",
        (
            Step("Plank", "پلانک", "سطح ۱"),
            Step("Side Bridge", "پلانک جانبی", "سطح ۲"),
            Step("Push Up to Side Plank", "شنای سوئدی به پلانک جانبی", "سطح ۳"),
        ),
    ),
    Ladder(
        "hinge",
        "لولا شدن باسن",
        {"9": 0.9, "3": 0.7, "13": 0.3},
        "نردبان الگوی بلند کردن بار از زمین",
        (
            Step("Good Morning", "گود مورنینگ", "سطح ۱"),
            Step("Romanian Deadlift", "ددلیفت رومانیایی", "سطح ۲"),
            Step("Barbell Deadlift", "ددلیفت هالتر", "سطح ۳"),
            Step("Kettlebell One-Legged Deadlift", "ددلیفت تک‌پا کتل‌بل", "سطح ۴"),
        ),
    ),
    Ladder(
        "lunge",
        "لانج",
        {"3": 0.7, "2": 0.5, "9": 0.4},
        "نردبان تک‌پا/راه رفتن",
        (
            Step("Bodyweight Walking Lunge", "لانج راه رفتنی با وزن بدن", "سطح ۱"),
            Step("Dumbbell Lunges", "لانج دمبل", "سطح ۲"),
            Step("Barbell Lunge", "لانج هالتر", "سطح ۳"),
        ),
    ),
    Ladder(
        "dip",
        "دیپ",
        {"3": 0.8, "5": 0.5, "10": 0.3},
        "نردبان فشاری پایین‌تنه/شانه‌ای",
        (
            Step("Bench Dips", "دیپ نیمکت", "سطح ۱"),
            Step("Dips - Triceps Version", "دیپ پشت بازو", "سطح ۲"),
            Step("Parallel Bar Dip", "دیپ میله‌های موازی", "سطح ۳"),
            Step("Ring Dips", "دیپ حلقه", "سطح ۴"),
        ),
    ),
    Ladder(
        "row",
        "کشش افقی",
        {"3": 0.7, "6": 0.5, "10": 0.4},
        "نردبان الگوی کششی افقی",
        (
            Step("One-Arm Dumbbell Row", "روئینگ تک‌دست دمبل", "سطح ۱"),
            Step("Bent Over Barbell Row", "روئینگ خمیده هالتر", "سطح ۲"),
        ),
    ),
    Ladder(
        "core",
        "شکم و پایداری مرکز",
        {"7": 0.9, "5": 0.5},
        "نردبان شکم پویا",
        (
            Step("Crunches", "کرانچ", "سطح ۱"),
            Step("Air Bike", "ایر بایک", "سطح ۲"),
            Step("Flat Bench Lying Leg Raise", "بالا آوردن پا روی نیمکت", "سطح ۳"),
            Step("Hanging Leg Raise", "بالا آوردن پا معلق", "سطح ۴"),
        ),
    ),
    Ladder(
        "glute-bridge",
        "پل سرینی",
        {"3": 0.6, "7": 0.5, "6": 0.4},
        "نردبان فعال‌سازی/قدرت سرینی",
        (
            Step("Butt Lift (Bridge)", "پل باسن", "سطح ۱"),
            Step("Single Leg Glute Bridge", "پل سرینی تک‌پا", "سطح ۲"),
            Step("Barbell Glute Bridge", "پل سرینی هالتر", "سطح ۳"),
        ),
    ),
)


def check_names(json_path: Path = DEFAULT_DATA) -> dict[str, str]:
    """نام هر پله باید دقیقاً در فایل منبع وجود داشته باشد — نگهبان یکپارچگی پیوندها."""
    rows = json.loads(json_path.read_text(encoding="utf-8"))
    by_name = {r["name"]: str(r["id"]) for r in rows}
    resolved: dict[str, str] = {}
    missing: list[str] = []
    for ladder in LADDERS:
        for step in ladder.steps:
            if step.catalog_name in by_name:
                resolved[step.catalog_name] = by_name[step.catalog_name]
            else:
                missing.append(f"{ladder.key}: {step.catalog_name}")
    if missing:
        raise ValueError("catalog rows missing for steps: " + "; ".join(missing))
    return resolved


def seed(session, resolved: dict[str, str]) -> dict:
    """ساخت idempotent نردبان‌ها + پیوند progression_key روی catalog."""
    stats = {"ladders": 0, "steps": 0, "linked": 0}
    for ladder in LADDERS:
        row = session.query(ProgressionLadder).filter_by(key=ladder.key).one_or_none()
        if row is None:
            row = ProgressionLadder(
                key=ladder.key,
                name_fa=ladder.name_fa,
                axis_focus=json.dumps(ladder.axis_focus, sort_keys=True),
                note=ladder.note,
            )
            session.add(row)
        else:
            row.name_fa = ladder.name_fa
            row.axis_focus = json.dumps(ladder.axis_focus, sort_keys=True)
            row.note = ladder.note
        stats["ladders"] += 1
        for step_no, step in enumerate(ladder.steps, start=1):
            external_id = resolved[step.catalog_name]
            existing = (
                session.query(ProgressionStep)
                .filter_by(ladder_key=ladder.key, step_no=step_no)
                .one_or_none()
            )
            if existing is None:
                session.add(
                    ProgressionStep(
                        ladder_key=ladder.key,
                        step_no=step_no,
                        catalog_external_id=external_id,
                        name_fa=step.name_fa,
                        note=step.note,
                    )
                )
            else:
                existing.catalog_external_id = external_id
                existing.name_fa = step.name_fa
                existing.note = step.note
            stats["steps"] += 1
            catalog_row = (
                session.query(CatalogExercise).filter_by(external_id=external_id).one_or_none()
            )
            if catalog_row is not None and not catalog_row.progression_key:
                catalog_row.progression_key = ladder.key
                stats["linked"] += 1
    session.commit()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="build progression ladders")
    parser.add_argument(
        "--check", action="store_true", help="only verify step names against source file"
    )
    args = parser.parse_args()
    resolved = check_names()
    if args.check:
        print(
            f"OK {len(LADDERS)} ladders, {sum(len(ladder.steps) for ladder in LADDERS)} steps resolved"
        )
        return 0
    session = get_session_factory()()
    try:
        stats = seed(session, resolved)
        print(json.dumps(stats, ensure_ascii=False))
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

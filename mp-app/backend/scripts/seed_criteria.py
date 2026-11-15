"""seed ابزارهای معیاری (rubric) برای محورهای بدون نُرم صدکی (M36-c2).

این ابزارها «طراحی ابزار MP» هستند (الگوی FMS-سبک بدون کپی ابزار تجاری) —
باندهایشان معیاری (criterion) است نه صدکی؛ روایی در پایلوت M40 ارزیابی می‌شود.
هر ردیب با `method="criterion"` ثبت می‌شود تا موتور امتیازدهی هرگز آن را «صدکی» جا نزند.

کاربرد: python scripts/seed_criteria.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.base import get_session_factory  # noqa: E402
from db.models.assessment import NormEntry  # noqa: E402

SOURCE = "MP criterion instrument v1 (M36) — روایی: candidate تا پایلوت M40"

# test_key → (axis, name_fa, bands)
RUBRICS: dict[str, tuple[int, str, dict]] = {
    "rubric_balance": (2, "تعادل (تک‌پا + دامنهٔ حرکتی)", {"0-39": "ضعیف", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
    "rubric_posture": (6, "وضعیت بدنی و تعادل عضلانی (چک‌لیست)", {"0-39": "ضعیف", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
    "plank_secs": (7, "پلانک (ایزومتریک مرکز)", {"0-29": "ضعیف", "30-59": "متوسط", "60-119": "خوب", "120+": "عالی"}),
    "rubric_coordination": (8, "هماهنگی و مهارت حرکتی (چک‌لیست)", {"0-39": "ضعیف", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
    "rubric_lifting": (9, "مکانیک بدن و بلند کردن بار (چک‌لیست تکنیک)", {"0-39": "پرخطر", "40-69": "نیازمند اصلاح", "70-89": "قابل قبول", "90-100": "درست"}),
    "rubric_breath": (11, "تنفس و کنترل فشار (مقیاس)", {"0-39": "ضعیف", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
    "rubric_recovery": (12, "بازیابی/خواب/مدیریت بار (خودگزارش)", {"0-39": "نیازمند توجه", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
    "rubric_body_awareness": (13, "پیشگیری آسیب و آگاهی بدن (چک‌لیست)", {"0-39": "ضعیف", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
    "rubric_foundational": (14, "مهارت‌های پایهٔ زندگی ورزشی (چک‌لیست)", {"0-39": "ضعیف", "40-69": "متوسط", "70-89": "خوب", "90-100": "عالی"}),
}


def seed(session) -> dict:
    stats = {"inserted": 0, "updated": 0}
    for test_key, (axis, name_fa, bands) in RUBRICS.items():
        existing = (
            session.query(NormEntry)
            .filter_by(test_key=test_key, sex="all", age_min=0, age_max=120)
            .one_or_none()
        )
        payload = {
            "name_fa": name_fa,
            "unit": "score0-100",
            "method": "criterion",
            "percentiles": "{}",
            "direction": "higher_better",
            "bands": json.dumps({"axis": axis, "labels": bands}, ensure_ascii=False, sort_keys=True),
            "sdc": None,
            "sdc_note": "ابزار معیاری — SDC ندارد",
            "source": SOURCE,
            "source_version": "mp-criterion-v1",
        }
        if existing is None:
            session.add(NormEntry(test_key=test_key, sex="all", age_min=0, age_max=120, **payload))
            stats["inserted"] += 1
        else:
            for key, value in payload.items():
                setattr(existing, key, value)
            stats["updated"] += 1
    session.commit()
    return stats


def main() -> int:
    session = get_session_factory()()
    try:
        print(json.dumps(seed(session), ensure_ascii=False))
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

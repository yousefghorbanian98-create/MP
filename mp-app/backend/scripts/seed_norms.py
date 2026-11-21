"""seed نُرم‌های آزمون‌های میدانی (M35-c1) — فقط دادهٔ مستند با منبع (E13).

منابع (بازبینی ۲۰۲۶-۱۱-۱۴):
- درصدک‌های شنای سوئدی: fitnessnorms.com/strength/push-ups/ (جداول سبک ACSM، جمع‌آوری ۲۰۲۶)
- درصدک‌های نشست و رسیدن: fitnessnorms.com/flexibility/sit-and-reach/
- SDC: گزارش‌های بازتست ACSM (media.cleveland.com/pdextra/other/push-ups.pdf —
  Institute for Aerobics Research 1991 + instituteofpersonaltrainers.com)

کاربرد:
    python scripts/seed_norms.py          # upsert در DB (idempotent)
    python scripts/seed_norms.py --count  # فقط شمارش ردیف‌های قابل seed
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from db.base import get_session_factory
from db.models.assessment import NormEntry

SOURCE_PUSHUP = "https://fitnessnorms.com/strength/push-ups/"
SOURCE_REACH = "https://fitnessnorms.com/flexibility/sit-and-reach/"
SOURCE_SDC = "https://media.cleveland.com/pdextra/other/push-ups.pdf + https://www.instituteofpersonaltrainers.com/"
SOURCE_GRIP = "https://fitnessnorms.com/strength/grip-strength/"
SOURCE_COOPER = "https://fitnessnorms.com/cardio/cooper-1-5-mile-run/"


@dataclass(frozen=True)
class NormRow:
    test_key: str
    name_fa: str
    unit: str
    sex: str
    age_min: int
    age_max: int
    percentiles: dict
    sdc: float | None
    sdc_note: str
    source: str
    source_version: str
    direction: str = "higher_better"


def _pushup(
    sex: str, age_min: int, age_max: int, p5: float, p25: float, p50: float, p75: float, p95: float
) -> NormRow:
    return NormRow(
        test_key="pushup_1min",
        name_fa="شنای سوئدی یک دقیقه‌ای",
        unit="reps",
        sex=sex,
        age_min=age_min,
        age_max=age_max,
        percentiles={"5": p5, "25": p25, "50": p50, "75": p75, "95": p95},
        sdc=9.0 if sex == "m" else 5.0,
        sdc_note="کوچک‌ترین تغییر واقعی بازتست (مردان ۹ / زنان ۵ تکرار)",
        source=SOURCE_PUSHUP + " | SDC: " + SOURCE_SDC,
        source_version="fitnessnorms-2026 + ACSM-SDC",
    )


def _reach(
    sex: str,
    age_min: int,
    age_max: int,
    p25: float,
    p75: float,
    p5: float | None = None,
    p50: float | None = None,
    p95: float | None = None,
) -> NormRow:
    percentiles: dict[str, float] = {"25": p25, "75": p75}
    if p5 is not None:
        percentiles["5"] = p5
    if p50 is not None:
        percentiles["50"] = p50
    if p95 is not None:
        percentiles["95"] = p95
    return NormRow(
        test_key="sit_and_reach",
        name_fa="نشست و رسیدن (انعطاف تنه‌ای-رانی)",
        unit="cm",
        sex=sex,
        age_min=age_min,
        age_max=age_max,
        percentiles=percentiles,
        sdc=4.5,
        sdc_note="کوچک‌ترین تغییر واقعی بازتست (۴٫۵ سانتی‌متر)",
        source=SOURCE_REACH + " | SDC: " + SOURCE_SDC,
        source_version="fitnessnorms-2026 + ACSM-SDC",
    )


def _grip(
    sex: str,
    age_min: int,
    age_max: int,
    p25: float,
    p75: float,
    p5: float | None = None,
    p50: float | None = None,
    p95: float | None = None,
) -> NormRow:
    percentiles: dict[str, float] = {"25": p25, "75": p75}
    if p5 is not None:
        percentiles["5"] = p5
    if p50 is not None:
        percentiles["50"] = p50
    if p95 is not None:
        percentiles["95"] = p95
    return NormRow(
        test_key="grip_kg",
        name_fa="قدرت گرفتن (دینامومتر دست)",
        unit="kg",
        sex=sex,
        age_min=age_min,
        age_max=age_max,
        percentiles=percentiles,
        sdc=None,
        sdc_note="SDC مستند برای این آزمون یافت نشد — قضاوت «تغییر واقعی» نامعلوم می‌ماند",
        source=SOURCE_GRIP,
        source_version="fitnessnorms-2026",
    )


def _cooper(
    sex: str, age_min: int, age_max: int, p5: float, p25: float, p50: float, p75: float, p95: float
) -> NormRow:
    # زمان‌ها به ثانیه تبدیل شده‌اند (منبع mm:ss) — کمتر بهتر
    return NormRow(
        test_key="cooper_1_5mile_sec",
        name_fa="دوی ۱٫۵ مایل (کوپر)",
        unit="sec",
        sex=sex,
        age_min=age_min,
        age_max=age_max,
        percentiles={"5": p5, "25": p25, "50": p50, "75": p75, "95": p95},
        sdc=None,
        direction="lower_better",
        sdc_note="SDC مستند برای این آزمون یافت نشد — قضاوت «تغییر واقعی» نامعلوم می‌ماند",
        source=SOURCE_COOPER,
        source_version="cooper-institute-2013-via-fitnessnorms",
    )


NORMS: tuple[NormRow, ...] = (
    # --- شنای سوئدی یک دقیقه‌ای (درصدک‌های ۵گانه) ---
    _pushup("m", 20, 29, 8, 22, 25, 29, 40),
    _pushup("m", 30, 39, 5, 17, 19, 22, 35),
    _pushup("m", 40, 49, 4, 13, 15, 17, 30),
    _pushup("m", 50, 59, 3, 10, 11, 13, 26),
    _pushup("m", 60, 69, 2, 8, 9, 11, 22),
    _pushup("f", 20, 29, 4, 15, 18, 21, 35),
    _pushup("f", 30, 39, 3, 13, 16, 20, 31),
    _pushup("f", 40, 49, 2, 11, 13, 15, 29),
    _pushup("f", 50, 59, 0, 7, 9, 11, 27),
    _pushup("f", 60, 69, 0, 5, 8, 12, 20),
    # --- نشست و رسیدن (۲۵ و ۷۵ برای همه؛ ۵/۵۰/۹۵ فقط ۶۰+ مستند است) ---
    _reach("m", 20, 24, 15.5, 33.5),
    _reach("f", 20, 24, 22.9, 38.8),
    _reach("m", 25, 29, 15.4, 33.4),
    _reach("f", 25, 29, 22.5, 39.1),
    _reach("m", 30, 34, 15.3, 32.9),
    _reach("f", 30, 34, 22.0, 39.3),
    _reach("m", 35, 39, 15.1, 32.3),
    _reach("f", 35, 39, 21.4, 39.2),
    _reach("m", 40, 44, 14.9, 31.6),
    _reach("f", 40, 44, 20.8, 38.8),
    _reach("m", 45, 49, 14.6, 30.7),
    _reach("f", 45, 49, 20.1, 38.3),
    _reach("m", 50, 54, 14.3, 29.8),
    _reach("f", 50, 54, 19.6, 37.8),
    _reach("m", 55, 59, 14.0, 28.9),
    _reach("f", 55, 59, 19.2, 37.5),
    _reach("m", 60, 64, 13.7, 28.0, p5=7.6, p50=20.9, p95=34.1),
    _reach("f", 60, 64, 19.1, 37.6, p5=11.3, p50=28.8, p95=43.4),
    _reach("m", 65, 69, 13.4, 27.1, p5=7.4, p50=20.3, p95=33.1),
    _reach("f", 65, 69, 19.0, 37.7, p5=11.1, p50=28.9, p95=43.8),
    # --- قدرت گرفتن (kg) — بازهٔ ۲۵/۷۵؛ ۵/۵۰/۹۵ فقط ۶۵-۶۹ مرد مستند است ---
    _grip("m", 20, 24, 41.9, 54.5),
    _grip("f", 20, 24, 24.9, 32.6),
    _grip("m", 25, 29, 43.5, 55.3),
    _grip("f", 25, 29, 25.4, 33.6),
    _grip("m", 30, 34, 43.6, 55.9),
    _grip("f", 30, 34, 25.4, 34.2),
    _grip("m", 35, 39, 43.0, 56.0),
    _grip("f", 35, 39, 25.1, 34.3),
    _grip("m", 40, 44, 42.0, 55.5),
    _grip("f", 40, 44, 24.8, 34.1),
    _grip("m", 45, 49, 40.6, 54.5),
    _grip("f", 45, 49, 24.1, 33.6),
    _grip("m", 50, 54, 39.0, 53.2),
    _grip("f", 50, 54, 23.4, 32.9),
    _grip("m", 55, 59, 37.2, 51.5),
    _grip("f", 55, 59, 22.6, 31.9),
    _grip("m", 60, 64, 35.2, 49.5),
    _grip("f", 60, 64, 21.6, 30.8),
    _grip("m", 65, 69, 33.1, 47.2, p5=23.7, p50=40.1, p95=56.8),
    _grip("f", 65, 69, 20.6, 29.4),
    _grip("m", 70, 74, 30.9, 44.7),
    _grip("f", 70, 74, 19.3, 27.9),
    _grip("m", 75, 79, 28.4, 41.9),
    _grip("f", 75, 79, 17.9, 26.2),
    _grip("m", 80, 84, 25.9, 39.0),
    _grip("f", 80, 84, 16.4, 24.4),
    _grip("m", 85, 89, 23.2, 35.9),
    _grip("f", 85, 89, 14.8, 22.4),
    # --- دوی ۱٫۵ مایل کوپر (ثانیه — کمتر بهتر) ---
    _cooper("m", 20, 29, 550, 634, 718, 805, 1006),
    _cooper("f", 20, 29, 620, 727, 855, 1003, 1265),
    _cooper("m", 30, 39, 571, 659, 745, 850, 1050),
    _cooper("f", 30, 39, 668, 788, 914, 1058, 1317),
    _cooper("m", 40, 49, 587, 692, 785, 900, 1119),
    _cooper("f", 40, 49, 695, 838, 973, 1119, 1407),
    _cooper("m", 50, 59, 627, 757, 873, 986, 1300),
    _cooper("f", 50, 59, 796, 947, 1085, 1255, 1575),
    _cooper("m", 60, 69, 680, 838, 979, 1150, 1558),
    _cooper("f", 60, 69, 868, 1054, 1208, 1400, 1746),
    _cooper("m", 70, 79, 745, 938, 1119, 1342, 1834),
    _cooper("f", 70, 79, 873, 1119, 1342, 1575, 2012),
)


def seed(session) -> dict:
    stats = {"inserted": 0, "updated": 0}
    for row in NORMS:
        existing = (
            session.query(NormEntry)
            .filter_by(test_key=row.test_key, sex=row.sex, age_min=row.age_min, age_max=row.age_max)
            .one_or_none()
        )
        payload = {
            "name_fa": row.name_fa,
            "unit": row.unit,
            "method": "percentile",
            "percentiles": json.dumps(row.percentiles, sort_keys=True),
            "bands": "{}",
            "direction": row.direction,
            "sdc": row.sdc,
            "sdc_note": row.sdc_note,
            "source": row.source,
            "source_version": row.source_version,
        }
        if existing is None:
            session.add(
                NormEntry(
                    test_key=row.test_key,
                    sex=row.sex,
                    age_min=row.age_min,
                    age_max=row.age_max,
                    **payload,
                )
            )
            stats["inserted"] += 1
        else:
            for key, value in payload.items():
                setattr(existing, key, value)
            stats["updated"] += 1
    session.commit()
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="seed field-test norm tables")
    parser.add_argument("--count", action="store_true", help="only print row count")
    args = parser.parse_args()
    if args.count:
        print(len(NORMS))
        return 0
    with get_session_factory()() as session:
        stats = seed(session)
        print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

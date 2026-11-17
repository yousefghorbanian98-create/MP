"""تست‌های جدول نُرم‌ها (M35-c1) — E13: هر ردیف با منبع، بدون عدد از حافظه."""

from __future__ import annotations

import json

from db.models.assessment import NormEntry
from scripts.seed_norms import NORMS, seed

VALID_P_KEYS = {"5", "25", "50", "75", "95"}


def test_norms_have_sources_and_valid_percentiles() -> None:
    assert len(NORMS) == 70
    for row in NORMS:
        assert row.source.startswith("https://")
        assert set(row.percentiles) <= VALID_P_KEYS
        assert {"25", "75"} <= set(row.percentiles)  # حداقل بازهٔ میانه در هر ردیف
        values = [row.percentiles[k] for k in sorted(row.percentiles, key=int)]
        assert values == sorted(values)  # صدک‌ها صعودی
        assert row.sdc is None or row.sdc > 0


def test_pushup_sdc_differs_by_sex() -> None:
    male = [r for r in NORMS if r.test_key == "pushup_1min" and r.sex == "m"]
    female = [r for r in NORMS if r.test_key == "pushup_1min" and r.sex == "f"]
    assert {r.sdc for r in male} == {9.0}
    assert {r.sdc for r in female} == {5.0}


def test_seed_upsert_idempotent(session) -> None:
    first = seed(session)
    second = seed(session)
    assert first == {"inserted": 70, "updated": 0}
    assert second == {"inserted": 0, "updated": 70}
    assert session.query(NormEntry).count() == 70
    row = (
        session.query(NormEntry)
        .filter_by(test_key="pushup_1min", sex="m", age_min=20, age_max=29)
        .one()
    )
    assert json.loads(row.percentiles) == {"5": 8, "25": 22, "50": 25, "75": 29, "95": 40}
    assert row.method == "percentile"
    assert row.unit == "reps"
    assert "fitnessnorms.com" in row.source

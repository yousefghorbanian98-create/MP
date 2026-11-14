"""تست‌های قفل معادلهٔ JP (E07/D-012) — هیچ محاسبه‌ای بدون مرجع مستقل تأییدشده."""

from __future__ import annotations

import pytest

from app.errors import ApiError
from modules.assessment.equations import (
    APPROVED_EQUATIONS,
    LOCKED_VERSION,
    jp7_body_fat,
    validate_jp7_raw,
)

VALID = {
    "chest": 10,
    "triceps": 8,
    "subscapular": 10,
    "suprailiac": 9,
    "abdomen": 15,
    "thigh": 12,
    "calf": 7,
}


def test_registry_is_empty_and_locked_version() -> None:
    assert APPROVED_EQUATIONS == {}  # هیچ معادلهٔ تأییدشده‌ای وجود ندارد
    assert LOCKED_VERSION.startswith("LOCKED")


def test_jp7_body_fat_always_locked_without_registry() -> None:
    with pytest.raises(ApiError) as e:
        jp7_body_fat(VALID, 30, "male", equation_id="anything")
    assert e.value.code == "equation_locked"


def test_validate_raw_accepts_valid_and_rejects_bad() -> None:
    clean = validate_jp7_raw(VALID, "male")
    assert clean["chest"] == 10.0
    with pytest.raises(ApiError):
        validate_jp7_raw({"chest": 1}, "male")  # ناقص
    with pytest.raises(ApiError):
        validate_jp7_raw({**VALID, "chest": -3}, "male")  # خارج از دامنه
    with pytest.raises(ApiError):
        validate_jp7_raw(
            {
                **VALID,
                "chest": 0,
                "triceps": 0,
                "subscapular": 0,
                "suprailiac": 0,
                "abdomen": 0,
                "thigh": 0,
                "calf": 0,
            },
            "male",
        )
    with pytest.raises(ApiError):
        validate_jp7_raw(VALID, "alien")  # جنسیت نامعتبر

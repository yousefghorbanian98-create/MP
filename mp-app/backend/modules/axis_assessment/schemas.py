"""اسکیماهای ارزیابی ۱۴ توانایی."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.ids import Id


class TestIn(BaseModel):
    test_key: str = Field(min_length=2, max_length=40)
    raw_value: float
    notes: str = ""


class AssessmentCreate(BaseModel):
    member_id: Id
    tests: list[TestIn] = Field(min_length=1)
    notes: str = ""


class TestOut(BaseModel):
    test_key: str
    raw_value: float
    unit: str = ""
    percentile: float | None = None
    quality: str = ""
    rule_version: str = ""
    norm_source: str = ""


class AxisScoreOut(BaseModel):
    axis: int
    name_fa: str
    score: float | None = None
    quality: str = "missing"
    decision_state: str = "unknown"
    decision_reason: str = ""


class MatrixOut(BaseModel):
    assessment_id: int
    member_id: int
    status: str
    axes: list[AxisScoreOut]
    summary: dict[str, int]
    rule_versions: dict[str, str]


class AssessmentOut(BaseModel):
    id: int
    member_id: int
    status: str
    notes: str = ""
    tests: list[TestOut] = []
    scores: list[AxisScoreOut] = []


class ReviewIn(BaseModel):
    action: str = Field(pattern="^(approve|reject)$")
    reason: str = ""

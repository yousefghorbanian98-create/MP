"""G4b — ستون LLM در ارزیابی.

قاعدهٔ محافظت‌شده: **بدون اجرای واقعی، عدد ساخته نمی‌شود.**
در محیط ساخت Ollama نیست؛ ادعای «LLM توافق داشت» تقلب پژوهشی است.
"""

from __future__ import annotations

from eval import llm_column
from eval.llm_column import LlmResult, build_prompt, compare, query_llm


class TestAvailability:
    def test_reports_unavailable_honestly(self, monkeypatch) -> None:
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://127.0.0.1:1")
        r = llm_column.availability("http://127.0.0.1:1")
        assert r.available is False
        assert "در دسترس نیست" in r.reason

    def test_query_does_not_invent_a_result_when_offline(self, monkeypatch) -> None:
        monkeypatch.setattr(
            llm_column,
            "availability",
            lambda base: LlmResult(available=False, model="x", reason="offline"),
        )
        r = query_llm({"goal": "hypertrophy", "weeks": 4})
        assert r.available is False
        assert r.parsed is None


class TestPrompt:
    def test_prompt_requests_strict_json(self) -> None:
        p = build_prompt({"goal": "hypertrophy", "weeks": 4, "injuries": ["knee"]})
        assert "STRICT JSON" in p
        assert "knee" in p
        assert "No commentary" in p

    def test_prompt_marks_absent_constraints_explicitly(self) -> None:
        p = build_prompt({"goal": "x", "weeks": 2, "injuries": []})
        assert "none" in p


class TestCompare:
    def test_not_comparable_when_llm_unavailable(self) -> None:
        r = compare(
            rule_problems=[],
            llm=LlmResult(available=False, model="llama", reason="offline"),
            forbidden=["squat"],
        )
        assert r["comparable"] is False
        assert r["llm"] is None
        assert "offline" in r["reason"]

    def test_not_comparable_when_response_is_not_json(self) -> None:
        r = compare(
            rule_problems=[],
            llm=LlmResult(
                available=True, model="x", reason="ok", raw_text="سلام، این یک برنامه است"
            ),
            forbidden=[],
        )
        assert r["comparable"] is False
        assert "JSON معتبر نبود" in r["reason"]

    def test_detects_forbidden_move_in_llm_output(self) -> None:
        parsed = {
            "weeks": [{"week_number": 1, "exercises": [{"name": "Barbell Squat", "sets": 3}]}]
        }
        r = compare(
            rule_problems=[],
            llm=LlmResult(available=True, model="x", reason="ok", raw_text="{}", parsed=parsed),
            forbidden=["squat"],
        )
        assert r["comparable"] is True
        assert r["llm"]["violations"] == 1
        assert r["llm"]["forbidden_used"] == ["barbell squat"]
        assert r["agreement"]["llm_only_violation"] is True

    def test_both_safe_when_nothing_forbidden_used(self) -> None:
        parsed = {"weeks": [{"week_number": 1, "exercises": [{"name": "Bench Press"}]}]}
        r = compare(
            rule_problems=[],
            llm=LlmResult(available=True, model="x", reason="ok", raw_text="{}", parsed=parsed),
            forbidden=["squat"],
        )
        assert r["agreement"]["both_safe"] is True

    def test_rule_engine_violation_is_reported_even_if_llm_is_safe(self) -> None:
        parsed = {"weeks": [{"week_number": 1, "exercises": [{"name": "Row"}]}]}
        r = compare(
            rule_problems=["ساختار نامعتبر"],
            llm=LlmResult(available=True, model="x", reason="ok", raw_text="{}", parsed=parsed),
            forbidden=["squat"],
        )
        assert r["rule_engine"]["violations"] == 1
        assert r["agreement"]["rule_only_violation"] is True

    def test_version_is_reported(self) -> None:
        r = compare(rule_problems=[], llm=LlmResult(False, "x", "offline"), forbidden=[])
        assert r["rule_version"] == llm_column.LLM_COLUMN_VERSION

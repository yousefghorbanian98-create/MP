"""G4b — ستون سوم ارزیابی: مقایسهٔ خروجی LLM با موتور قواعد.

## سؤال پژوهشی
«آیا یک مدل زبانی محلی می‌تواند برنامهٔ تمرینی به‌قدر موتور قاعده‌محور
ایمن و ساختارمند بسازد؟» این ستون سومِ فصل نتایج است: قواعد، استاندارد
طلایی، LLM.

## صداقت روش
Ollama در محیط ساخت در دسترس **نیست**. بنابراین:
- اداپتور واقعی نوشته شده و با `OLLAMA_BASE_URL` کار می‌کند؛
- اگر در دسترس نباشد، خروجی `available: false` با دلیل است، **نه**
  یک عدد ساختگی. گزارش‌دهی «LLM ۹۲٪ توافق داشت» بدون اجرای واقعی،
  تقلب پژوهشی است.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

# فقط http/https پذیرفته می‌شود. بدون این بررسی، هر کسی می‌تواند با
# OLLAMA_BASE_URL=file:///etc/passwd محتوای فایل محلی را بخواند
# (bandit B310).
ALLOWED_SCHEMES = ("http", "https")


def _url(base: str, path: str) -> str:
    """URL امن می‌سازد؛ scheme غیرمجاز را رد می‌کند."""
    full = f"{base.rstrip('/')}{path}"
    scheme = urllib.parse.urlparse(full).scheme
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"scheme «{scheme}» مجاز نیست — فقط http/https")
    return full


LLM_COLUMN_VERSION = "llm-column-1.0"
DEFAULT_MODEL = os.environ.get("MP_LLM_MODEL", "llama3.1")
DEFAULT_BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
TIMEOUT_SECONDS = 60


@dataclass
class LlmResult:
    available: bool
    model: str
    reason: str
    raw_text: str | None = None
    parsed: dict | None = None


def availability(base_url: str = DEFAULT_BASE) -> LlmResult:
    """بررسی در دسترس بودن Ollama — بدون فرض."""
    try:
        tags_url = _url(base_url, "/api/tags")  # scheme در _url محدود شده
        with urllib.request.urlopen(tags_url, timeout=5) as r:  # nosec B310
            data = json.loads(r.read().decode())
        models = [m.get("name", "") for m in data.get("models", [])]
        return LlmResult(
            available=True,
            model=DEFAULT_MODEL,
            reason=f"Ollama در دسترس است ({len(models)} مدل نصب‌شده)",
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        return LlmResult(
            available=False,
            model=DEFAULT_MODEL,
            reason=f"Ollama در دسترس نیست ({type(e).__name__}) — ستون LLM قابل پر کردن نیست",
        )


def build_prompt(scenario: dict) -> str:
    """پرامپت ساختاریافته — درخواست JSON، نه متن آزاد."""
    return (
        "You are a strength coach. Produce a training program as STRICT JSON only.\n"
        f"Goal: {scenario.get('goal')}\n"
        f"Weeks: {scenario.get('weeks')}\n"
        f"Sessions per week: {scenario.get('days_per_week', 3)}\n"
        f"Injuries / constraints: {scenario.get('injuries') or 'none'}\n"
        'Schema: {"weeks":[{"week_number":int,"exercises":[{"day":int,"order":int,'
        '"name":str,"sets":int,"reps":"8-12","load_pct":int,"rest_seconds":int}]}]}\n'
        "No commentary, only JSON."
    )


def query_llm(
    scenario: dict, *, base_url: str = DEFAULT_BASE, model: str = DEFAULT_MODEL
) -> LlmResult:
    """پرسش از LLM محلی. اگر در دسترس نباشد، صادقانه می‌گوید."""
    status = availability(base_url)
    if not status.available:
        return status

    payload = json.dumps(
        {"model": model, "prompt": build_prompt(scenario), "stream": False, "format": "json"}
    ).encode()
    req = urllib.request.Request(
        _url(base_url, "/api/generate"),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as r:  # nosec B310
            body = json.loads(r.read().decode())
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as e:
        return LlmResult(
            available=False,
            model=model,
            reason=f"پاسخ LLM دریافت نشد ({type(e).__name__})",
        )

    text = body.get("response", "")
    try:
        parsed = json.loads(text)
    except ValueError:
        parsed = None
    return LlmResult(
        available=True,
        model=model,
        reason="پاسخ دریافت شد",
        raw_text=text,
        parsed=parsed,
    )


def compare(*, rule_problems: list[str], llm: LlmResult, forbidden: list[str]) -> dict:
    """مقایسهٔ ستون LLM با موتور قواعد.

    اگر LLM در دسترس نباشد، خروجی صریحاً `comparable: false` است.
    عدد نبودن بهتر از عدد دروغین است.
    """
    if not llm.available:
        return {
            "comparable": False,
            "reason": llm.reason,
            "rule_engine": {"violations": len(rule_problems)},
            "llm": None,
            "rule_version": LLM_COLUMN_VERSION,
        }

    if llm.parsed is None:
        return {
            "comparable": False,
            "reason": "پاسخ LLM JSON معتبر نبود — قابل مقایسه با ساختار برنامه نیست",
            "rule_engine": {"violations": len(rule_problems)},
            "llm": {"model": llm.model, "raw_length": len(llm.raw_text or "")},
            "rule_version": LLM_COLUMN_VERSION,
        }

    names = [
        str(ex.get("name", "")).lower()
        for week in llm.parsed.get("weeks", []) or []
        for ex in week.get("exercises", []) or []
    ]
    violations = [n for n in names if any(f.lower() in n for f in forbidden)]
    return {
        "comparable": True,
        "reason": "هر دو ستون ساختار یکسانی دارند",
        "rule_engine": {"violations": len(rule_problems)},
        "llm": {
            "model": llm.model,
            "exercises": len(names),
            "violations": len(violations),
            "forbidden_used": violations,
        },
        "agreement": {
            "both_safe": len(rule_problems) == 0 and len(violations) == 0,
            "llm_only_violation": len(rule_problems) == 0 and len(violations) > 0,
            "rule_only_violation": len(rule_problems) > 0 and len(violations) == 0,
        },
        "rule_version": LLM_COLUMN_VERSION,
    }

"""M60 / R2 — گیتِ route-guard: هر مسیر یا guard دارد یا عمومیِ مستند است.

پیش از این فقط `test_routes_artifact.py` بود که «فهرست مسیرها» را با یک
آرتیفکت مقایسه می‌کرد — یک endpoint تازهٔ بدون guard می‌توانست بی‌صدا رد شود
(آرتیفکت به‌روز می‌شد و تست سبز). این تست همان شکاف را می‌بندد.

سه چیز سنجیده می‌شود:
1. قواعد (`evaluate`) روی دادهٔ ساختگی — تا مطمئن شویم گیت واقعاً چیزی را رد
   می‌کند، نه اینکه همیشه سبز باشد.
2. خودِ اپ واقعی — هیچ مسیری بدون guard و بدون ثبت در PUBLIC نیست.
3. `PUBLIC` مرده نماند — اگر مسیری guard بگیرد، ورودش در PUBLIC باید حذف شود.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
GATE = BACKEND / "scripts" / "route_guard_gate.py"


def _load():
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    spec = importlib.util.spec_from_file_location("route_guard_gate", GATE)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


gate = _load()


def test_unlisted_unguarded_route_is_rejected():
    problems, _ = gate.evaluate([("GET", "/api/v1/secret/new", set())])
    assert problems and "secret/new" in problems[0]


def test_guarded_route_is_accepted():
    problems, stale = gate.evaluate([("GET", "/api/v1/secret/new", {"permission"})])
    assert problems == [] and stale == []


def test_public_route_is_accepted():
    problems, _ = gate.evaluate([("GET", "/health", set())])
    assert problems == []


def test_public_entry_that_became_guarded_is_flagged():
    """اگر مسیری guard گرفت ولی هنوز در PUBLIC مانده، گیت باید هشدار دهد."""
    problems, stale = gate.evaluate([("GET", "/health", {"permission"})])
    assert problems == []
    assert stale and "/health" in stale[0]


def test_real_app_has_no_unguarded_unknown_route():
    from app.main import create_app

    rows = gate.collect_routes(create_app())
    assert len(rows) > 100, f"پیمایش مسیرها شکست (فقط {len(rows)} مسیر) — FastAPI عوض شده؟"
    problems, stale = gate.evaluate(rows)
    assert problems == [], "مسیر بدون guard: " + "; ".join(problems)
    assert stale == [], "PUBLIC مرده: " + "; ".join(stale)


def test_public_entries_all_have_reasons():
    """هر مسیر عمومی باید دلیل مکتوب داشته باشد — «عمومی» نباید پیش‌فرض باشد."""
    for key, reason in gate.PUBLIC.items():
        assert reason and len(reason) > 10, f"دلیل کافی نیست برای {key}"

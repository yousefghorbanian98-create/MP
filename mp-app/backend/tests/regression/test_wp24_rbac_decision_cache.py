"""WP 2.4 / F‑05 — تصمیم RBAC باید روی درخواست تکراری دوباره در casbin ارزیابی نشود.

قبل از اصلاح: هر `enforce` به `casbin.Enforcer.enforce` می‌رسید (compile/eval روی هر درخواست،
منبع SystemError زیر بار). بعد از اصلاح: تصمیم برای (نقش، مسیر، متد) یک‌بار محاسبه و در کش
محدود نگه داشته می‌شود.
"""

from __future__ import annotations

import re
import threading

import pytest

from app.metrics import metrics
from security import rbac

ROLES = ["member", "coach", "reception", "manager", "admin", "super_admin"]
METHODS = ["GET", "POST", "PATCH", "PUT", "DELETE"]


def _clear() -> None:
    # قبل از اصلاح تابع وجود ندارد؛ تست باید به‌خاطر رفتار (تعداد ارزیابی) قرمز شود، نه به‌خاطر نبودن نام.
    clear = getattr(rbac, "enforce_cache_clear", None)
    if clear is not None:
        clear()


@pytest.fixture(autouse=True)
def _fresh_cache():
    _clear()
    yield
    _clear()


def test_repeated_identical_request_hits_casbin_once(monkeypatch) -> None:
    enforcer = rbac.get_enforcer()
    calls = {"n": 0}
    original = enforcer.enforce

    def spy(*args):
        calls["n"] += 1
        return original(*args)

    monkeypatch.setattr(enforcer, "enforce", spy)
    results = {rbac.enforce("member", "/api/v1/members/7", "GET") for _ in range(50)}
    assert results == {True}
    assert calls["n"] == 1, f"casbin ارزیابی شد {calls['n']} بار؛ باید ۱ بار"


def test_cache_is_bounded() -> None:
    info = getattr(rbac, "_decide", None)
    assert info is not None, "کش تصمیم وجود ندارد"
    size = info.cache_info().maxsize
    assert size is not None and size <= 8192


def test_concurrent_decisions_match_single_thread_and_do_not_error() -> None:
    paths = [
        ("member", "/api/v1/members/1", "GET"),
        ("member", "/api/v1/payments/finance/summary", "GET"),
        ("reception", "/api/v1/payments/finance/summary", "GET"),
        ("manager", "/api/v1/admin/permissions", "GET"),
        ("super_admin", "/api/v1/shop/products", "POST"),
        ("coach", "/api/v1/expenses", "POST"),
    ]
    expected = {p: rbac.enforce(*p) for p in paths}
    _clear()

    errors: list[BaseException] = []
    mismatches: list[tuple] = []
    lock = threading.Lock()

    def work(tid: int) -> None:
        try:
            for i in range(200):
                p = paths[(tid + i) % len(paths)]
                got = rbac.enforce(*p)
                if got != expected[p]:
                    with lock:
                        mismatches.append((p, got))
        except BaseException as exc:  # noqa: BLE001
            with lock:
                errors.append(exc)

    ts = [threading.Thread(target=work, args=(i,)) for i in range(80)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert not errors, errors[:3]
    assert not mismatches, mismatches[:3]


def test_decision_metrics_are_exported() -> None:
    rbac.enforce("member", "/api/v1/members/1", "GET")
    rbac.enforce("member", "/api/v1/payments/finance/summary", "GET")
    text = metrics.render()
    assert "mp_rbac_decisions_total" in text
    assert 'decision="allow"' in text and 'decision="deny"' in text


def test_distinct_numeric_ids_share_one_casbin_evaluation(monkeypatch) -> None:
    """کش نباید با هر شناسهٔ عددی جدید دوباره در casbin ارزیابی شود (کاردینالیتی شناسه)."""
    enforcer = rbac.get_enforcer()
    calls = {"n": 0}
    original = enforcer.enforce

    def spy(*args):
        calls["n"] += 1
        return original(*args)

    monkeypatch.setattr(enforcer, "enforce", spy)
    for member_id in range(1, 1001):
        rbac.enforce("member", f"/api/v1/members/{member_id}", "GET")
    assert calls["n"] == 1, f"casbin ارزیابی شد {calls['n']} بار برای ۱۰۰۰ شناسه؛ باید ۱ بار"


def test_numeric_id_normalisation_preserves_every_decision() -> None:
    """هم‌ارزی: برای هر مسیر نمونه، تصمیم با مسیر خام و با مسیر نرمال‌شده (شناسه→:id) یکی است."""
    from app.main import app as fastapi_app

    samples: set[str] = set()
    for tpl in fastapi_app.openapi()["paths"]:
        for value in ("1", "42", "99999"):
            samples.add(re.sub(r"\{[^}]+\}", value, tpl))
    for _, obj, _ in rbac.POLICIES:
        samples.add(obj.replace("*", "7").replace(":id", "7"))
    assert len(samples) > 100

    for path in sorted(samples):
        for role in ROLES:
            for method in METHODS:
                raw = rbac._decide_raw(role, path, method)
                norm = rbac._decide(role, rbac._normalise_path(path), method)
                assert raw == norm, (role, method, path)

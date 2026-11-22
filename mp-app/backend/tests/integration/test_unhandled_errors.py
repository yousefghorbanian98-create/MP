"""M60/R18 — ۵۰۰ باید قالب خطای پروژه داشته باشد، نه بدنهٔ خالی.

پیدا شده با `scripts/dast.py` (جانشین ZAP/nuclei که دانلودشان مسدود است).
سه مسیر واقعی کرش می‌کردند و در تولید پاسخشان **بدنهٔ خالی** بود؛ کلاینت
فلاتر آن را «خطای سرور (۵۰۰)» نشان می‌داد و اپراتور نمی‌دانست چه درخواستی
شکسته است.

این تست‌ها سه چیز را قفل می‌کنند:
  ۱. پاسخ ۵۰۰ همان `{"error": {"code": "internal_error"}}` است
  ۲. هیچ جزئیات فنی (SQL، مسیر فایل، نام کلاس) در پاسخ نیست
  ۳. شمارندهٔ متریک بالا می‌رود تا در `/metrics` دیده شود

و دو «رفع ریشه‌ای» که DAST پیدا کرد:
  ۴. `offset` بزرگ ← ۴۲۲ (قبلاً `OverflowError` روی SQLite ← ۵۰۰)
  ۵. شناسهٔ مسیر بزرگ‌تر از ۲^۵۳ ← ۴۲۲ با `PathId`
"""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

from ._metrics import METRICS_AUTH

_counter = itertools.count(880001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/unhandled.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    # raise_server_exceptions=False = همان رفتاری که uvicorn در تولید دارد؛
    # بدون این، TestClient استثنا را بالا می‌دهد و هندلر هرگز اجرا نمی‌شود.
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    reset_engine()


def _headers(role: str = "super_admin") -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"u-{n}", role=role)
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _break_service(monkeypatch) -> None:
    """سرویس را می‌شکنیم تا خطای *غیرمنتظره* تولید شود.

    چرا monkeypatch و نه ورودی عجیب: مسیرهای واقعی DAST حالا با اعتبارسنجی
    ۴۲۲ می‌دهند (که خوب است). برای سنجش خودِ هندلر باید یک خطای واقعیِ
    غیرمنتظره در لایهٔ سرویس بسازیم — هندلر نباید به منبع خطا وابسته باشد.
    """

    def boom(*a, **kw):
        raise RuntimeError("simulated storage failure")

    from modules.membership import service as membership_service

    monkeypatch.setattr(membership_service, "list_members", boom)


def test_unexpected_error_has_project_shape(client, monkeypatch) -> None:
    _break_service(monkeypatch)
    r = client.get("/api/v1/members", headers=_headers())
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "internal_error"
    assert body["error"]["message"].strip()


def test_unexpected_error_does_not_leak_internals(client, monkeypatch) -> None:
    _break_service(monkeypatch)
    text = client.get("/api/v1/members", headers=_headers()).text
    for leak in ("RuntimeError", "simulated storage failure", "Traceback", "sqlalchemy"):
        assert leak.lower() not in text.lower(), f"نشت جزئیات: {leak}"


def test_unexpected_error_increments_metric(client, monkeypatch) -> None:
    from app.metrics import metrics

    _break_service(monkeypatch)

    def _count() -> float:
        # `metrics` یک singleton سراسری است و تست‌های قبلی هم روی آن نوشته‌اند؛
        # پس «افزایش» را می‌سنجیم، نه «شروع از صفر» (این یک‌بار تست را
        # به‌غلط قرمز کرد).
        line = 'mp_unhandled_errors_total{path="/api/v1/members",type="RuntimeError"} '
        for row in metrics.render().splitlines():
            if row.startswith(line):
                return float(row[len(line) :])
        return 0.0

    before = _count()
    client.get("/api/v1/members", headers=_headers())
    assert _count() == before + 1
    # و همان از مسیر عمومی متریک هم دیده می‌شود
    assert "mp_unhandled_errors_total" in client.get("/api/v1/metrics", headers=METRICS_AUTH).text


def test_huge_offset_is_rejected_before_touching_db(client) -> None:
    """رفع ریشه‌ای: سقف `offset` باید ۴۲۲ بدهد، نه ۵۰۰ (قبلاً OverflowError)."""
    r = client.get("/api/v1/members", params={"offset": 10**30}, headers=_headers())
    assert r.status_code == 422, r.text


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/assessments/limb/member/9007199254740992/report",
        "/api/v1/assessments/member/9007199254740992",
    ],
)
def test_oversized_path_id_is_422_not_500(client, path) -> None:
    """`PathId` (سقف ۲^۵۳) باید پیش از لایهٔ داده رد کند."""
    r = client.get(path, headers=_headers())
    assert r.status_code == 422, f"{path} → {r.status_code} {r.text[:200]}"


def test_known_good_request_still_works(client) -> None:
    """کنترل مثبت: هندلر نباید پاسخ‌های سالم را دست بزند."""
    r = client.get("/api/v1/members", headers=_headers())
    assert r.status_code == 200


# ── M60/R18 — خطای Integrity باید ۴xx باشد، نه ۵۰۰ ──
#
# DAST با idهای تصادفی این‌ها را پیدا کرد: `POST /programs/set-feedback`,
# `/nutrition/weight-logs`, `/classes`, `/members/memberships`، … هر کدام
# `IntegrityError` می‌دادند و ۵۰۰ می‌گرفتند — یعنی «سرویس خراب است» در حالی
# که مشکل ورودی کاربر بود.
def test_foreign_key_violation_is_422(client) -> None:
    h = _headers()
    r = client.post(
        "/api/v1/classes",
        json={"name": "کلاس تست", "capacity": 5, "coach_id": 987654321},
        headers=h,
    )
    assert r.status_code == 422, f"{r.status_code} {r.text[:300]}"
    assert r.json()["error"]["code"] == "invalid_reference"


def test_integrity_payload_mapping() -> None:
    """نگاشت نوع خطا به کد/پیام — بدون DB، تا قواعد مستقل از sqlite سنجیده شوند."""
    from sqlalchemy.exc import IntegrityError

    from app.unhandled import _integrity_payload

    fk = IntegrityError("INSERT", {}, Exception("FOREIGN KEY constraint failed"))
    assert _integrity_payload(fk)[0] == 422
    uniq = IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed: users.phone"))
    assert _integrity_payload(uniq)[0] == 409
    assert _integrity_payload(uniq)[1]["error"]["code"] == "conflict"


def test_integrity_violation_not_counted_as_unhandled(client) -> None:
    """خطای ۴xx نباید شمارندهٔ ۵۰۰ را بالا ببرد — وگرنه هشدارها بی‌معنا می‌شوند."""
    from app.metrics import metrics

    before = metrics.render().count("mp_unhandled_errors_total")
    client.post(
        "/api/v1/classes",
        json={"name": "کلاس", "capacity": 5, "coach_id": 987654321},
        headers=_headers(),
    )
    assert metrics.render().count("mp_unhandled_errors_total") == before


# ── M60/R18 — سقف شناسه در *مسیر* (middleware) ──
#
# ۴۱ endpoint شناسه را `int` خالی می‌گیرند. اصلاح تک‌تک امضاها را رها کردیم و
# قاعده را یک‌جا در middleware گذاشتیم تا endpointهای آینده هم پوشش بگیرند.
@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/shop/products/999999999999999999999999999999",
        "/api/v1/notifications/reminders/member/100000000000000000000",
        "/api/v1/programs/member/340282366920938463463374607431768211456",
        "/api/v1/chat/conversations/999999999999999999999999/messages",
    ],
)
def test_oversized_path_segment_is_422(client, path) -> None:
    r = client.get(path, headers=_headers())
    assert r.status_code == 422, f"{path} → {r.status_code} {r.text[:150]}"
    assert r.json()["error"]["code"] == "invalid_id"


def test_id_guard_does_not_block_normal_ids(client) -> None:
    """کنترل منفی: شناسهٔ معمولی (حتی با صفر ابتدایی) نباید ۴۲۲ بگیرد."""
    r = client.get("/api/v1/shop/products/42", headers=_headers())
    assert r.status_code != 422, r.text


def test_update_manifest_survives_unicode_digits() -> None:
    """`GET /updates/manifest?current=²` (پایان‌بندی عمومی) قبلاً ۵۰۰ می‌داد.

    علت: `"²".isdigit()` در پایتون True است ولی `int("²")` ValueError می‌دهد.
    این مسیر **بدون احراز هویت** است، پس هر کسی می‌توانست آن را بترکاند.
    """
    from modules.updates.service import parse_version

    assert parse_version("²") == (0, 0, 0)
    assert parse_version("1.2.3") == (1, 2, 3)
    assert parse_version("v2.0") == (2, 0, 0)
    # رشتهٔ بسیار بزرگ هم نباید به int بی‌کران تبدیل شود
    assert parse_version("9" * 40)[0] == 10**6

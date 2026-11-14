"""تست‌های گزارش محرمانهٔ ۸بخشی + نگاشت ۱۳ محور (M24)."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from db.base import get_session_factory, init_db, reset_engine
from modules.reporting.axes import AXES_13, DOMAIN14_TO_AXES, axes_for_domains

_counter = itertools.count(900001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    from modules.auth.router import limiter

    db_url = f"sqlite:///{tmp_path}/rep_test.db"
    monkeypatch.setattr(settings, "database_url", db_url)
    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


@pytest.fixture()
def auth():
    def _auth(role: str = "coach") -> dict:
        from app.security.jwt import create_access_token
        from db.models import User

        n = next(_counter)
        with get_session_factory()() as s:
            u = User(phone=f"09{n:09d}", full_name=f"{role}-{n}", role=role)
            s.add(u)
            s.commit()
            token = create_access_token(u.id, u.role)
            return {"Authorization": f"Bearer {token}"}

    return _auth


def test_mapping_covers_all_13_axes() -> None:
    mapped = {a for axes in DOMAIN14_TO_AXES.values() for a in axes}
    assert mapped == {a["id"] for a in AXES_13}  # هر ۱۳ محور حداقل یک دامنه دارد


def test_axes_unknown_not_zero() -> None:
    out = axes_for_domains({})  # بدون ارزیابی
    assert len(out) == 13
    assert all(v["status"] == "insufficient_data" for v in out.values())


def test_axes_status_from_scores() -> None:
    out = axes_for_domains({1: 5, 4: 0.5, 5: 3})
    assert out["axis-11"]["status"] in ("covered_in_other_task", "education_monitoring")
    assert out["axis-02"]["status"] == "direct_training"  # امتیاز پایین ← تمرین مستقیم


def test_confidential_report_full_structure(client, auth):
    coach = auth("coach")
    member = client.post(
        "/api/v1/members", json={"phone": "09125550001", "full_name": "ورزشکار نمونه", "goal": "hypertrophy"},
        headers=coach,
    ).json()
    # ارزیابی ۱۴ دامنه
    scores = [{"domain": d, "score": 3} for d in range(1, 15)]
    client.post("/api/v1/assessments", json={"member_id": member["id"], "scores": scores}, headers=coach)
    # JP7 خام (قفل)
    skinfolds = {"chest": 10, "triceps": 8, "subscapular": 10, "suprailiac": 9,
                 "abdomen": 15, "thigh": 12, "calf": 7}
    client.post(
        "/api/v1/assessments/jp7",
        json={"member_id": member["id"], "age": 30, "gender": "male",
              "skinfolds_mm": skinfolds, "quality": "good", "method": "caliper"},
        headers=coach,
    )
    r = client.get(f"/api/v1/reports/confidential/{member['id']}", headers=coach)
    assert r.status_code == 200
    rep = r.json()
    for i in range(1, 9):
        assert f"section_{i}_" in str(rep.keys()) or any(k.startswith(f"section_{i}_") for k in rep)
    assert rep["section_1_identity"]["full_name"] == "ورزشکار نمونه"
    assert len(rep["section_5_axes_13"]) == 13
    assert rep["section_6_decision_chain"][0]["rule"].startswith("rules-1.0")
    assert rep["section_4_derived"][0]["value"] is None  # قفل D-012
    assert rep["section_7_versions"]["ai_model_used"] is None
    missing = rep["section_3_data_snapshot"]["explicitly_missing"]
    assert any("وزن" in m for m in missing)  # مفقود صریح (E01)
    # HTML راست‌چین (D-020)
    h = client.get(f"/api/v1/reports/confidential/{member['id']}?format=html", headers=coach)
    assert h.status_code == 200
    assert 'dir="rtl"' in h.text and "ورزشکار نمونه" in h.text
    assert "زنجیرهٔ داده" in h.text

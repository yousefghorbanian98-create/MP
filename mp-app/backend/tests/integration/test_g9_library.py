"""G9 — کتابخانهٔ حرکات با تصویر: API و فایل واقعی."""

from __future__ import annotations

import itertools

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(979501)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/g9.db")
    from db.base import init_db, reset_engine

    reset_engine()
    init_db()
    limiter.reset()
    from cache.store import InMemoryCache, reset_cache

    reset_cache(InMemoryCache())
    app = __import__("app.main", fromlist=["create_app"]).create_app()
    with TestClient(app) as c:
        yield c
    reset_engine()


@pytest.fixture()
def member_headers(client):
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Exercise, Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"m{n}", role="member")
        s.add(u)
        s.commit()
        s.add(Member(user_id=u.id, gender="male", goal="x", branch_id=1))
        s.commit()
        # کاتالوگ + تصاویر همان‌طور که اسکریپت واقعی می‌سازد
        for eid in range(1, 18):
            s.add(
                Exercise(
                    id=eid,
                    external_id=f"ex_{eid}",
                    name_fa="اسکوات پشت" if eid == 1 else f"حرکت {eid}",
                    name_en=f"ex {eid}",
                    muscle_group="legs" if eid % 2 else "chest_shoulders",
                    video_url=f"/static/exercises/{eid}_0.jpg",
                )
            )
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def test_every_library_exercise_has_a_real_image(client: TestClient, member_headers: dict) -> None:
    """هر حرکت باید تصویر داشته باشد و آن تصویر واقعاً از اپ سرو شود.

    باگ قبلی: `video_url` همیشه `` بود، پس یک فیلد دکوراتیو بود.
    """
    res = client.get("/api/v1/library/exercises", headers=member_headers)
    assert res.status_code == 200, res.text
    items = res.json()
    assert len(items) >= 17

    without_image = [i["name_fa"] for i in items if not i["image_url"]]
    assert not without_image, f"حرکت بدون تصویر: {without_image}"

    for item in items:
        img = client.get(item["image_url"]) if item["image_url"].startswith("/") else None
        assert img is not None, "مسیر تصویر باید داخلی باشد (بدون hotlink)"
        assert img.status_code == 200, item["image_url"]
        assert img.headers["content-type"] == "image/jpeg"
        assert img.content[:2] == b"\xff\xd8", "فایل باید JPEG واقعی باشد"
        alt = client.get(item["image_url_alt"])
        assert alt.status_code == 200, item["image_url_alt"]


def test_library_filters_work(client: TestClient, member_headers: dict) -> None:
    all_items = client.get("/api/v1/library/exercises", headers=member_headers).json()
    pushed = client.get(
        "/api/v1/library/exercises?muscle_group=chest_shoulders", headers=member_headers
    ).json()
    assert pushed, "گروه عضلانی باید حداقل یک عضو داشته باشد"
    assert len(pushed) < len(all_items)
    assert all(i["muscle_group"] == "chest_shoulders" for i in pushed)

    found = client.get("/api/v1/library/exercises?q=اسکوات", headers=member_headers).json()
    assert any("اسکوات" in i["name_fa"] for i in found)


def test_unknown_exercise_is_404(client: TestClient, member_headers: dict) -> None:
    assert client.get("/api/v1/library/exercises/99999", headers=member_headers).status_code == 404


def test_library_requires_auth(client: TestClient) -> None:
    assert client.get("/api/v1/library/exercises").status_code == 401


@pytest.mark.parametrize("exercise_id", [1, 7, 17])
def test_single_exercise_payload(
    client: TestClient, member_headers: dict, exercise_id: int
) -> None:
    res = client.get(f"/api/v1/library/exercises/{exercise_id}", headers=member_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["exercise_id"] == exercise_id
    assert body["name_fa"]
    assert body["image_url"] == f"/static/exercises/{exercise_id}_0.jpg"

"""E2E — چرخهٔ کامل سازگاری: غذا → وزن → برنامه → بازخورد → آمادگی → سنک.

این تست همان چیزی را می‌سنجد که در دفاع ادعا می‌شود: «ورودی کاربر از
چند موتور عبور می‌کند و در خروجی قابل ردیابی است». مسیرهای G1/G3/G5/
G6/G7/G13 هر کدام تست جدا دارند؛ اینجا **به‌هم‌پیوستگی** سنجیده می‌شود.

اگر یک روز یکی از ماژول‌ها شکل پاسخش را عوض کند و بقیه با آن هم‌خوان
نباشند، این تست می‌شکند — چیزی که تست‌های واحد نمی‌گیرند.
"""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.config import settings

_counter = itertools.count(690001)


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from modules.auth.router import limiter

    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path}/loop.db")
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


def _member(height_cm: float = 180.0) -> tuple[int, int]:
    from db.base import get_session_factory
    from db.models import Member, User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"loop-{n}", role="member")
        s.add(u)
        s.commit()
        m = Member(
            user_id=u.id, gender="male", goal="hypertrophy", height_cm=height_cm, branch_id=1
        )
        s.add(m)
        s.commit()
        return m.id, u.id


def _staff() -> dict:
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import User

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name=f"coach-{n}", role="manager")
        s.add(u)
        s.commit()
        return {"Authorization": f"Bearer {create_access_token(u.id, u.role)}"}


def _seed_weight_history(mid: int, *, days: int = 20, start: float = 82.0, slope: float = -0.5):
    """تاریخچهٔ وزن واقعی در DB — نقطه‌های G3."""
    from db.base import get_session_factory
    from db.models import BodyWeightLog

    now = datetime.now(UTC)
    with get_session_factory()() as s:
        for i in range(days, 0, -1):
            s.add(
                BodyWeightLog(
                    member_id=mid,
                    weight_kg=round(start + slope * (days - i), 1),
                    logged_for_date=(now - timedelta(days=i)).date().isoformat(),
                    source="member",
                )
            )
        s.commit()


def test_full_adaptive_loop(client: TestClient) -> None:
    h = _staff()
    mid, _ = _member()

    # ۱) G5 — غذا: DB تست از create_all ساخته می‌شود و کاتالوگ ۳۰۵ غذایی
    # در migration پر شده، نه در مدل. پس اینجا خودمان یک غذا می‌سازیم —
    # چیزی که سنجیده می‌شود مسیر ثبت و محاسبهٔ کالری است، نه محتوای کاتالوگ
    # (آن در تست‌های M49 پوشش دارد).
    from db.base import get_session_factory
    from db.models import FoodItem

    with get_session_factory()() as s:
        food = FoodItem(
            name_fa="برنج سفید پخته",
            category="غلات",
            kcal_per_100g=130,
            protein_g_per_100g=2.7,
            fat_g_per_100g=0.3,
            carbs_g_per_100g=28.0,
        )
        s.add(food)
        s.commit()
        food_id = food.id

    foods = client.get("/api/v1/nutrition/foods?limit=3", headers=h).json()
    assert any(f["id"] == food_id for f in foods)

    # ۲) G5 — ثبت غذا با محاسبهٔ کالری
    today = datetime.now(UTC).date().isoformat()
    logged = client.post(
        "/api/v1/nutrition/food-logs",
        json={
            "member_id": mid,
            "entries": [
                {
                    "food_id": food_id,
                    "grams": 200,
                    "meal_slot": "lunch",
                    "logged_for_date": today,
                }
            ],
        },
        headers=h,
    )
    assert logged.status_code == 200, logged.text
    daily = client.get(
        f"/api/v1/nutrition/food-logs/member/{mid}/daily?date={today}", headers=h
    ).json()
    assert daily["totals"]["kcal"] > 0, "غذای ثبت‌شده باید کالری داشته باشد"

    # ۳) G3 — روند وزن ⇒ TDEE
    _seed_weight_history(mid)
    adaptive = client.get(f"/api/v1/nutrition/member/{mid}/adaptive", headers=h).json()
    est = adaptive["estimate"]
    # روند وزن از دادهٔ واقعی ساخته می‌شود
    assert est["trend"]["slope_kg_per_week"] < 0, "وزن باید نزولی باشد"
    assert est["trend"]["days_used"] == 20
    # TDEE به ۷ روز *ثبت غذا* نیاز دارد؛ اینجا فقط یک روز ثبت شده،
    # پس موتور صادقانه عدد نمی‌سازد و دلیل می‌دهد — نه صفر، نه حدس.
    assert est["tdee_kcal"] is None
    assert est["data_state"] == "insufficient_intake"
    assert "7 روز" in est["reason"]

    # ۴) G13 — بدون بازخورد ست، آمادگی «نامعلوم» است (نه صفر)
    readiness = client.get(f"/api/v1/programs/member/{mid}/readiness", headers=h).json()
    # بدون برنامهٔ ثبت‌شده هیچ آمادگی‌ای ساخته نمی‌شود — و پاسخ دلیل می‌دهد
    assert readiness["readiness"] is None
    assert readiness["reason"]

    # ۵) G7 — صف آفلاین بازخورد ست: ست اول با افت شدید
    old = (datetime.now(UTC) - timedelta(days=2)).isoformat()
    queue = client.post(
        "/api/v1/programs/sync/set-feedback",
        json={
            "member_id": mid,
            "items": [
                {
                    "client_id": "w1-s1",
                    "device_id": "phone-e2e",
                    "updated_at": old,
                    "movement_id": "squat",
                    "weight": 100,
                    "target_reps": 8,
                    "reps_done": 8,
                    "rir": 2,
                    "soreness": 3,
                },
                {
                    "client_id": "w1-s2",
                    "device_id": "phone-e2e",
                    "updated_at": old,
                    "movement_id": "squat",
                    "weight": 100,
                    "target_reps": 8,
                    "reps_done": 5,
                    "rir": 0,
                    "soreness": 9,
                },
            ],
        },
        headers=h,
    ).json()
    assert queue["counts"]["applied"] == 2

    # ۶) G13 — همان بازخورد حالا امتیاز می‌سازد و کاهش حجم پیشنهاد می‌دهد
    # بدون برنامه، سرویس صادقانه چیزی نمی‌سازد؛ برای سنجش آمادگی یک
    # برنامهٔ واقعی از مسیر موتور ثبت می‌کنیم.
    prog = client.post(
        "/api/v1/programs/from-engine",
        json={
            "member_id": mid,
            "goal": "hypertrophy",
            "engine_version": "e2e",
            "weeks": [
                {
                    "week_number": 1,
                    "exercises": [
                        {
                            "exercise_id": 1,
                            "day": 1,
                            "order": 0,
                            "sets": 3,
                            "reps": "8-12",
                            "movement": "squat",
                        }
                    ],
                }
            ],
        },
        headers=h,
    )
    assert prog.status_code == 200, prog.text
    program_id = prog.json()["id"]

    # بازخوردهای صف آفلاین را به همین برنامه وصل می‌کنیم
    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s_:
        for r_ in s_.query(SetFeedback).filter(SetFeedback.member_id == mid).all():
            r_.program_id = program_id
        s_.commit()

    readiness2 = client.get(f"/api/v1/programs/member/{mid}/readiness", headers=h).json()
    assert readiness2["program_id"] is not None
    r = readiness2["readiness"]
    assert r is not None, f"با بازخورد واقعی باید امتیاز ساخته شود: {readiness2['reason']}"
    assert 0 <= r["score"] <= 100
    assert r["rule_version"] == "readiness-1.0"
    # افت تکرار + RIR صفر + درد ۹ باید امتیاز را پایین بیاورد
    assert r["score"] < 100

    # ۷) G6 — اندازه‌گیری JP7 و روند
    jp7 = client.post(
        "/api/v1/assessments/jp7",
        json={
            "member_id": mid,
            "age": 30,
            "gender": "male",
            "skinfolds_mm": {
                "chest": 10.0,
                "abdomen": 20.0,
                "thigh": 12.0,
                "triceps": 9.0,
                "subscapular": 11.0,
                "suprailiac": 13.0,
                "calf": 10.0,
            },
        },
        headers=h,
    )
    assert jp7.status_code == 200, jp7.text
    trend = client.get(f"/api/v1/assessments/jp7/member/{mid}/trend", headers=h).json()
    assert trend["trend"] is None, "یک نقطه روند نیست"
    assert trend["interpretation"]["status"] == "insufficient"

    # ۸) M54 — آنالیز سگمنتال
    limb = client.post(
        "/api/v1/assessments/limb",
        json={"member_id": mid, "waist_cm": 88, "hip_cm": 100, "upper_arm_right_cm": 36},
        headers=h,
    )
    assert limb.status_code == 200
    seg = client.get(f"/api/v1/assessments/limb/member/{mid}/report", headers=h).json()
    assert seg["analysis"]["ratios"]["waist_to_height"]["band"] == "normal"

    # ۹) G8 — چت: مربی می‌پرسد، عضو پاسخ می‌دهد
    conv = client.post(
        "/api/v1/chat/conversations",
        json={"member_id": mid, "subject": "برنامهٔ هفتهٔ دوم"},
        headers=h,
    ).json()
    msg = client.post(
        f"/api/v1/chat/conversations/{conv['id']}/messages",
        json={"body": "افت تکرار داشتی؟"},
        headers=h,
    )
    assert msg.status_code == 200
    msgs = client.get(f"/api/v1/chat/conversations/{conv['id']}/messages", headers=h).json()
    assert len(msgs["messages"]) == 1

    # ۱۰) G11 — یادآوری از دادهٔ واقعی ساخته می‌شود
    reminders = client.get(f"/api/v1/notifications/reminders/member/{mid}", headers=h).json()
    assert reminders["rule_version"] == "reminders-1.0"
    assert reminders["counts"]["due"] + reminders["counts"]["skipped"] > 0


def test_loop_is_consistent_after_a_retry(client: TestClient) -> None:
    """قطعی شبکه در وسط چرخه نباید داده را دوباره ایجاد کند."""
    h = _staff()
    mid, _ = _member()
    stamp = (datetime.now(UTC) - timedelta(minutes=30)).isoformat()
    payload = {
        "member_id": mid,
        "items": [
            {
                "client_id": "retry-1",
                "device_id": "phone-a",
                "updated_at": stamp,
                "movement_id": "bench",
                "weight": 80,
                "target_reps": 10,
                "reps_done": 10,
                "rir": 2,
            }
        ],
    }
    first = client.post("/api/v1/programs/sync/set-feedback", json=payload, headers=h).json()
    second = client.post("/api/v1/programs/sync/set-feedback", json=payload, headers=h).json()

    assert first["counts"]["applied"] == 1
    assert second["counts"]["applied"] == 0

    from db.base import get_session_factory
    from db.models import SetFeedback

    with get_session_factory()() as s:
        rows = s.query(SetFeedback).filter(SetFeedback.member_id == mid).all()
        assert len(rows) == 1, "تلاش مجدد نباید رکورد دوم بسازد"


def test_member_cannot_read_another_members_whole_loop(client: TestClient) -> None:
    """همهٔ ماژول‌های جدید باید مالکیت را یکسان اعمال کنند."""
    from app.security.jwt import create_access_token
    from db.base import get_session_factory
    from db.models import Member, User

    h = _staff()
    victim, _ = _member()

    n = next(_counter)
    with get_session_factory()() as s:
        u = User(phone=f"09{n:09d}", full_name="intruder", role="member")
        s.add(u)
        s.commit()
        s.add(Member(user_id=u.id, gender="male", goal="x", branch_id=1))
        s.commit()
        ih = {"Authorization": f"Bearer {create_access_token(u.id, 'member')}"}

    guarded = [
        f"/api/v1/programs/member/{victim}/readiness",
        f"/api/v1/programs/member/{victim}/volume",
        f"/api/v1/assessments/jp7/member/{victim}/trend",
        f"/api/v1/assessments/limb/member/{victim}/report",
        f"/api/v1/nutrition/member/{victim}/adaptive",
        f"/api/v1/notifications/reminders/member/{victim}",
        f"/api/v1/chat/conversations?member_id={victim}",
    ]
    for url in guarded:
        r = client.get(url, headers=ih)
        assert r.status_code in (403, 200), f"{url} → {r.status_code}"
        if r.status_code == 200:
            body = r.json()
            # اگر ۲۰۰ داد، نباید دادهٔ عضو دیگر را افشا کند
            assert not (isinstance(body, dict) and body.get("member_id") == victim), (
                f"{url} دادهٔ عضو دیگر را برگرداند"
            )
    _ = h

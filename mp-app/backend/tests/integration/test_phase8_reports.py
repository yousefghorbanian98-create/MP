"""فاز ۸ لوپ ۳ — گزارش زمان‌بندی‌شده (QF-23).

# قرارداد

| مورد | قاعده |
|---|---|
| تک‌فعال | یک job key در یک روزِ تهران فقط یک گزارش می‌سازد (دوبار اجرا/ری‌استارت/دو worker) |
| منطقهٔ زمانی | مرز روز بر اساس `Asia/Tehran` است، نه UTC |
| عدد حساس | اعلان/ممیزی فقط «آماده است» می‌گوید؛ مبلغ‌ها فقط با `finance.read` از endpoint می‌آیند |
| مجوز | اجرا `finance.write`، خواندن `finance.read`؛ نقش بدون مجوز ۴۰۳ |
| ناشناخته | job_key ناشناخته ۴۰۰ `unknown_job` |

# چرا این تست

پیش از این گزارش دوره‌ای فقط دستی و از صفحهٔ تحلیل خوانده می‌شد؛ هیچ تضمینی
نبود که اجرای دوباره (ری‌استارت scheduler یا دو worker) گزارش تکراری نسازد و
هیچ سابقه‌ای از «چه روزی اجرا شد» نبود.

# آنچه تست نمی‌کند
- ارسال push/ایمیل به مالک — کانال بیرونی وجود ندارد (`BLOCKED`).
- انتخاب زمان اجرا در UI (فقط backend؛ UI در گام بعد اگر لازم شد).
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import ReportRun
from modules.reports import schedule as report_schedule
from tests.integration._actors import create_actor


def _feb(client: TestClient, headers: dict, job: str = "daily_finance", **params):
    return client.post(
        f"/api/v1/finance/reports/schedule/{job}/run", json=params or {}, headers=headers
    )


def test_daily_report_is_idempotent_per_tehran_day(client: TestClient) -> None:
    _ = client  # فیچر schema را می‌سازد
    morning = datetime(2026, 3, 15, 6, 0, tzinfo=UTC)

    with get_session_factory()() as s:
        first = report_schedule.run_daily_finance(s, now=morning)
        second = report_schedule.run_daily_finance(s, now=morning.replace(hour=9))

    assert first["created"] is True
    assert second["created"] is False
    assert first["run_date"] == second["run_date"] == "2026-03-15"
    with get_session_factory()() as s:
        rows = s.query(ReportRun).filter(ReportRun.job_key == "daily_finance").all()
        assert len(rows) == 1


def test_tehran_midnight_is_the_day_boundary_not_utc(client: TestClient) -> None:
    _ = client
    # ۲۰:۴۵ UTC ۱۵ مارس = ۰۰:۱۵ ۱۶ مارس به وقت تهران (+۰۳:۳۰)
    late = datetime(2026, 3, 15, 20, 45, tzinfo=UTC)
    before = datetime(2026, 3, 15, 20, 15, tzinfo=UTC)

    with get_session_factory()() as s:
        assert report_schedule.tehran_date(before).isoformat() == "2026-03-15"
        assert report_schedule.tehran_date(late).isoformat() == "2026-03-16"
        a = report_schedule.run_daily_finance(s, now=before)
        b = report_schedule.run_daily_finance(s, now=late)
    assert a["run_date"] == "2026-03-15"
    assert b["run_date"] == "2026-03-16"
    assert b["created"] is True


def test_unknown_job_is_rejected_without_side_effects(client: TestClient) -> None:
    _ = client
    with get_session_factory()() as s:
        try:
            report_schedule.run_job(s, "does_not_exist")
        except Exception as exc:  # noqa: BLE001 - قرارداد: ApiError با کد
            assert getattr(exc, "code", "") == "unknown_job"
        else:  # pragma: no cover
            raise AssertionError("job ناشناخته باید رد شود")


def test_run_requires_finance_write_and_read_requires_finance_read(client: TestClient) -> None:
    no_grant = create_actor("manager")
    reader = create_actor("manager", ["finance.read"])
    writer = create_actor("manager", ["finance.write"])

    denied = _feb(client, no_grant)
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "permission_required"
    assert _feb(client, reader).status_code == 403
    assert client.get("/api/v1/finance/reports/schedule", headers=reader).status_code == 200
    assert client.get("/api/v1/finance/reports/schedule", headers=no_grant).status_code == 403

    ok = _feb(client, writer)
    assert ok.status_code == 200, ok.text
    assert ok.json()["created"] is True


def test_repeat_run_returns_the_same_record_instead_of_duplicating(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write", "finance.read"])
    first = _feb(client, staff)
    second = _feb(client, staff)
    assert first.status_code == second.status_code == 200
    assert first.json()["run_date"] == second.json()["run_date"]
    assert second.json()["created"] is False


def test_report_numbers_only_behind_finance_read(client: TestClient) -> None:
    """بدنهٔ اجرا جمع‌ها را برمی‌گرداند؛ اعلان/ممیزی نباید مبلغ داشته باشد."""
    staff = create_actor("manager", ["finance.write", "finance.read"])
    run = _feb(client, staff).json()
    detail = client.get(f"/api/v1/finance/reports/daily/{run['run_date']}", headers=staff)
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert set(body) >= {"run_date", "payments_total_rial", "expenses_total_rial", "net_rial"}
    assert set(body) >= {"payments_count", "expenses_count"}

    no_read = create_actor("manager", ["finance.write"])
    assert (
        client.get(f"/api/v1/finance/reports/daily/{run['run_date']}", headers=no_read).status_code
        == 403
    )

    # پیام ممیزی/اعلان: عدد پولی در متن نیست (فقط «آماده است»).
    from db.models import AuditLog

    with get_session_factory()() as s:
        rows = s.query(AuditLog).filter(AuditLog.action == "scheduled_report_ready").all()
    assert rows, "اجرای گزارش باید یک ردیف ممیزی بدون عدد داشته باشد"
    for row in rows:
        assert "rial" not in (row.detail or "").lower()
        assert "total" not in (row.detail or "").lower()


def test_schedule_status_lists_runs_and_next_run(client: TestClient) -> None:
    staff = create_actor("manager", ["finance.write", "finance.read"])
    _feb(client, staff)
    res = client.get("/api/v1/finance/reports/schedule", headers=staff)
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["jobs"][0]["job_key"] == "daily_finance"
    assert body["jobs"][0]["runs"], "حداقل یک اجرا باید ثبت شده باشد"
    assert body["next_run_utc"].endswith("Z")

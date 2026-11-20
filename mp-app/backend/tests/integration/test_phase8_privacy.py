"""فاز ۸ لوپ ۶ — حریم و نگهداری داده (QF-28).

# قرارداد

| مورد | قاعده |
|---|---|
| پیش‌نمایش | `GET /admin/retention` فقط می‌شمارد؛ چیزی حذف نمی‌کند |
| اجرا | `POST /admin/retention/run` فقط ردیف‌های قدیمی‌تر از سیاست را حذف می‌کند |
| پول و دفتر | `payments`, `ledger_entries`, `expenses`, `report_runs` هرگز پاک نمی‌شوند |
| ممیزی | هر اجرا یک ردیف `retention_run` با شمارش دارد، بدون دادهٔ شخصی |
| دسترسی | فقط `super_admin`؛ admin/manager/coach/member ۴۰۳ |

# چرا این تست

«سیاست نگهداری» تا امروز یک سند بود، نه کد. بدون کد، لاگ‌های ممیزی و
پیام‌های مصرف‌شده تا ابد می‌مانند و ادعای «حداقل‌سازی داده» قابل اثبات نیست.

# آنچه تست نمی‌کند
- تأیید حقوقی مدت‌ها (`BLOCKED`: تصمیم مالک/وکیل) — اعداد پیش‌فرض محافظه‌کارانه‌اند.
- حذف/بی‌هویت‌سازی دادهٔ عضو به درخواست خودش (right-to-erasure) — خارج از این لوپ.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from db.base import get_session_factory
from db.models import (
    AuditLog,
    InboxMessage,
    LedgerEntry,
    Member,
    Notification,
    Payment,
    User,
)
from modules.privacy import retention
from tests.integration._actors import create_actor


def _old(days: int, now: datetime) -> datetime:
    return now - timedelta(days=days)


def _fixture(now: datetime) -> dict:
    with get_session_factory()() as s:
        user = User(phone="09350000001", full_name="عضو-حریم", role="member")
        s.add(user)
        s.flush()
        member = Member(user_id=user.id, goal="fat_loss", constraints="[]")
        s.add(member)
        s.flush()

        s.add_all(
            [
                AuditLog(
                    actor_user_id=None,
                    action="old_audit",
                    entity_type="x",
                    detail="{}",
                    created_at=_old(400, now),
                ),
                AuditLog(
                    actor_user_id=None,
                    action="new_audit",
                    entity_type="x",
                    detail="{}",
                    created_at=_old(10, now),
                ),
                InboxMessage(topic="t", dedup_key="old", processed_at=_old(120, now)),
                InboxMessage(topic="t", dedup_key="new", processed_at=_old(3, now)),
                Notification(
                    member_id=member.id,
                    title="قدیمی خوانده‌شده",
                    kind="general",
                    read_at=_old(300, now),
                    created_at=_old(300, now),
                ),
                Notification(
                    member_id=member.id,
                    title="قدیمی نخوانده",
                    kind="general",
                    created_at=_old(300, now),
                ),
            ]
        )
        payment = Payment(
            member_id=member.id, amount_rial=1_000_000, status="paid", paid_at=_old(900, now)
        )
        s.add(payment)
        s.flush()
        s.add(
            LedgerEntry(
                member_id=member.id,
                amount_rial=1_000_000,
                kind="charge",
                source_type="wallet",
                note="قدیمی",
                created_at=_old(900, now),
            )
        )
        s.commit()
        return {"member_id": member.id, "payment_id": payment.id}


def test_preview_counts_without_deleting(client: TestClient) -> None:
    now = datetime.now(UTC)
    _fixture(now)
    with get_session_factory()() as s:
        before = s.query(AuditLog).count()
        preview = retention.preview(s, now=now)
        after = s.query(AuditLog).count()
    assert before == after
    assert preview["policies"]["audit_logs"]["expired"] >= 1


def test_run_deletes_only_expired_rows_and_keeps_money(client: TestClient) -> None:
    now = datetime.now(UTC)
    ids = _fixture(now)
    with get_session_factory()() as s:
        result = retention.run(s, now=now)
        s.commit()

    assert result["deleted"]["audit_logs"] >= 1
    assert result["deleted"]["inbox_messages"] >= 1
    assert result["deleted"]["notifications"] == 1  # فقط خوانده‌شدهٔ قدیمی

    with get_session_factory()() as s:
        actions = {row.action for row in s.query(AuditLog).all()}
        assert "new_audit" in actions
        assert "old_audit" not in actions
        # پول، دفتر و هزینه دست‌نخورده‌اند — نگهداری مالی مشمول این سیاست نیست.
        assert s.get(Payment, ids["payment_id"]) is not None
        assert s.query(LedgerEntry).count() >= 1
        assert s.query(Notification).count() == 1


def test_each_run_is_audited_without_personal_data(client: TestClient) -> None:
    now = datetime.now(UTC)
    _fixture(now)
    with get_session_factory()() as s:
        retention.run(s, now=now)
        s.commit()
        rows = s.query(AuditLog).filter(AuditLog.action == "retention_run").all()
    assert len(rows) == 1
    detail = rows[0].detail or ""
    assert "deleted" in detail
    assert "عضو-حریم" not in detail
    assert "09350000001" not in detail


def test_only_super_admin_can_preview_or_run(client: TestClient) -> None:
    for role in ("admin", "manager", "coach", "member"):
        headers = create_actor(role)
        assert client.get("/api/v1/admin/retention", headers=headers).status_code == 403
        assert (
            client.post("/api/v1/admin/retention/run", json={}, headers=headers).status_code == 403
        )

    owner = create_actor("super_admin")
    assert client.get("/api/v1/admin/retention", headers=owner).status_code == 200
    ran = client.post("/api/v1/admin/retention/run", json={}, headers=owner)
    assert ran.status_code == 200, ran.text
    assert "deleted" in ran.json()


def test_policies_are_explicit_and_in_days() -> None:
    policies = retention.POLICIES
    assert set(policies) >= {"audit_logs", "inbox_messages", "read_notifications"}
    for name, policy in policies.items():
        assert policy["days"] > 0, name
        assert policy["why"].strip(), name

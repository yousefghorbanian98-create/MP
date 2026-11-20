"""سیاست نگهداری داده — به‌صورت کد، نه سند (QF-28).

# اصل

داده‌ای که برای عملیات لازم نیست، نباید برای همیشه بماند. اما «پاک کردن» هم
بی‌قید خطرناک است: پول و دفتر نباید با یک job حذف شوند. پس سیاست سه بخش دارد:

1. **پاک‌شدنی:** لاگ ممیزی، پیام‌های مصرف‌شدهٔ inbox، اعلان‌های خوانده‌شده،
   گزارش‌های قدیمی.
2. **دست‌نزن:** `payments`, `ledger_entries`, `expenses`, `expense_revisions`,
   `report_runs`, ارزیابی‌های عضو، فایل فیش‌ها. (نگهداری مالی/بالینی قاعدهٔ
   جدا و تأیید حقوقی می‌خواهد → `BLOCKED`.)
3. **همیشه ممیزی:** هر اجرا با شمارش ثبت می‌شود، بدون هیچ دادهٔ شخصی.

# چرا پیش‌نمایش جدا از اجراست

برای اینکه مالک بتواند ببیند «چه چیزی می‌رود» پیش از رفتن. پیش‌نمایش هیچ
ردیفی را تغییر نمی‌دهد.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from db.models import AuditLog, InboxMessage, Notification, ReportRun
from modules.admin.service import audit

# روزها محافظه‌کارانه انتخاب شده‌اند؛ تغییرشان تصمیم صاحب داده است، نه کد.
POLICIES: dict[str, dict] = {
    "audit_logs": {
        "days": 365,
        "why": "ممیزی یک سال؛ کوتاه‌تر، پیگیری تخلف/اختلاف را ناممکن می‌کند",
    },
    "inbox_messages": {
        "days": 90,
        "why": "کلید dedup فقط تا افق retry معنا دارد؛ بعدش فقط حجم است",
    },
    "read_notifications": {
        "days": 180,
        "why": "اعلان خوانده‌شده شش ماه؛ اعلان نخوانده حذف نمی‌شود",
    },
    "report_runs": {
        "days": 730,
        "why": "سابقهٔ گزارش مالی دو سال برای مقایسهٔ سالانه",
    },
}
IMMUTABLE_TABLES = (
    "payments",
    "ledger_entries",
    "expenses",
    "expense_revisions",
    "outbox_dead_letters",
)


def _cutoff(days: int, now: datetime) -> datetime:
    return now - timedelta(days=days)


def _counts(db: Session, now: datetime) -> dict[str, dict]:
    out: dict[str, dict] = {}
    limits = {name: _cutoff(policy["days"], now) for name, policy in POLICIES.items()}
    out["audit_logs"] = {
        "days": POLICIES["audit_logs"]["days"],
        "why": POLICIES["audit_logs"]["why"],
        "expired": db.scalar(
            select(func.count(AuditLog.id)).where(AuditLog.created_at < limits["audit_logs"])
        )
        or 0,
    }
    out["inbox_messages"] = {
        "days": POLICIES["inbox_messages"]["days"],
        "why": POLICIES["inbox_messages"]["why"],
        "expired": db.scalar(
            select(func.count(InboxMessage.id)).where(
                InboxMessage.processed_at < limits["inbox_messages"]
            )
        )
        or 0,
    }
    out["read_notifications"] = {
        "days": POLICIES["read_notifications"]["days"],
        "why": POLICIES["read_notifications"]["why"],
        "expired": db.scalar(
            select(func.count(Notification.id)).where(
                Notification.read_at.is_not(None),
                Notification.read_at < limits["read_notifications"],
            )
        )
        or 0,
    }
    out["report_runs"] = {
        "days": POLICIES["report_runs"]["days"],
        "why": POLICIES["report_runs"]["why"],
        "expired": db.scalar(
            select(func.count(ReportRun.id)).where(ReportRun.created_at < limits["report_runs"])
        )
        or 0,
    }
    return out


def preview(db: Session, *, now: datetime | None = None) -> dict:
    """فقط شمارش؛ هیچ حذفی انجام نمی‌شود."""
    moment = now or datetime.now(UTC)
    return {
        "generated_at": moment.isoformat(),
        "policies": _counts(db, moment),
        "immutable": list(IMMUTABLE_TABLES),
    }


def run(db: Session, *, now: datetime | None = None, commit: bool = False) -> dict:
    """حذف ردیف‌های منقضی طبق سیاست؛ خروجی: شمارش حذف‌شده‌ها."""
    moment = now or datetime.now(UTC)
    counts = _counts(db, moment)
    deleted = {
        "audit_logs": db.execute(
            delete(AuditLog).where(
                AuditLog.created_at < _cutoff(POLICIES["audit_logs"]["days"], moment)
            )
        ).rowcount
        or 0,
        "inbox_messages": db.execute(
            delete(InboxMessage).where(
                InboxMessage.processed_at < _cutoff(POLICIES["inbox_messages"]["days"], moment)
            )
        ).rowcount
        or 0,
        "notifications": db.execute(
            delete(Notification).where(
                Notification.read_at.is_not(None),
                Notification.read_at < _cutoff(POLICIES["read_notifications"]["days"], moment),
            )
        ).rowcount
        or 0,
        "report_runs": db.execute(
            delete(ReportRun).where(
                ReportRun.created_at < _cutoff(POLICIES["report_runs"]["days"], moment)
            )
        ).rowcount
        or 0,
    }
    audit(
        db,
        None,
        "retention_run",
        "retention",
        None,
        {"deleted": deleted, "candidates": {k: v["expired"] for k, v in counts.items()}},
        commit=False,
    )
    db.flush()
    if commit:
        db.commit()
    return {
        "ran_at": moment.isoformat(),
        "deleted": deleted,
        "policies": counts,
        "immutable": list(IMMUTABLE_TABLES),
    }

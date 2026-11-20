"""روتر گزارش محرمانه — فقط staff (دادهٔ حساس؛ E09/E10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from app.deps import CurrentUser, DbSession, require_permission
from app.security.grants import require_grant
from modules.reporting.service import build_confidential_report, render_html

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(require_permission())]
)


@router.get(
    "/confidential/{member_id}",
    summary="گزارش محرمانهٔ ۸بخشی (JSON یا HTML)",
    dependencies=[Depends(require_grant("reports.confidential"))],
)
def confidential_report(
    member_id: int,
    db: DbSession,
    user: CurrentUser,
    format: str = Query("json", pattern="^(json|html)$"),
):
    # گزارش شامل پیکرسنجی/سلامت است. RBAC فقط نقش را می‌سنجد؛ مالکیت و
    # ثبت ممیزی باید اینجا باشد (semgrep: مسیر member_id بدون کنترل).
    from app.security.ownership import ensure_member_scope
    from modules.admin.service import audit

    ensure_member_scope(db, user, member_id)
    report = build_confidential_report(db, member_id)
    audit(db, user.id, "confidential_report_viewed", "member", member_id, {"format": format})
    if format == "html":
        return HTMLResponse(render_html(report))
    return report

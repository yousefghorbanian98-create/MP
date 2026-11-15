"""روتر گزارش محرمانه — فقط staff (دادهٔ حساس؛ E09/E10)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse

from app.deps import DbSession, require_permission
from modules.reporting.service import build_confidential_report, render_html

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(require_permission())]
)


@router.get("/confidential/{member_id}", summary="گزارش محرمانهٔ ۸بخشی (JSON یا HTML)")
def confidential_report(
    member_id: int,
    db: DbSession,
    format: str = Query("json", pattern="^(json|html)$"),
):
    report = build_confidential_report(db, member_id)
    if format == "html":
        return HTMLResponse(render_html(report))
    return report

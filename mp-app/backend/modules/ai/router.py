"""روتر هوشمندی تمرین (M29)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.deps import DbSession, require_roles
from engine.autoreg import suggest_next_weight

router = APIRouter(prefix="/ai", tags=["ai"])


class SuggestWeightIn(BaseModel):
    last_weight: float = Field(..., gt=0)
    reps_done: int = Field(..., ge=0)
    target_reps: int = Field(..., gt=0)
    rpe: float | None = Field(None, ge=1, le=10)


@router.post(
    "/suggest-weight",
    summary="وزنهٔ پیشنهادی بعدی (autoreg-1.0)",
    dependencies=[Depends(require_roles("admin", "manager", "coach", "member"))],
)
def suggest_weight(
    payload: SuggestWeightIn,
    db: DbSession,  # noqa: ARG001
):
    return suggest_next_weight(
        last_weight=payload.last_weight,
        reps_done=payload.reps_done,
        target_reps=payload.target_reps,
        rpe=payload.rpe,
    )

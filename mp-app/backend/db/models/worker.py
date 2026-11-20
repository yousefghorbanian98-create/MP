"""وضعیت workerها — heartbeat برای تشخیص «مرده ولی بی‌صدا» (QF-27)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class WorkerHeartbeat(Base):
    """آخرین نشانهٔ حیات هر worker؛ یک ردیف برای هر `worker_key`."""

    __tablename__ = "worker_heartbeats"

    id: Mapped[int] = mapped_column(primary_key=True)
    worker_key: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_result: Mapped[str] = mapped_column(Text, nullable=False, server_default="{}")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

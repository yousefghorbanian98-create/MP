"""Repository ماژول assessment."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import Assessment14Domain, JacksonPollockMeasurement


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, assessment_id: int) -> Assessment14Domain | None:
        return self.db.get(Assessment14Domain, assessment_id)

    def add(self, assessment: Assessment14Domain) -> Assessment14Domain:
        self.db.add(assessment)
        self.db.commit()
        self.db.refresh(assessment)
        return assessment

    def list_by_member(self, member_id: int) -> list[Assessment14Domain]:
        return list(
            self.db.scalars(
                select(Assessment14Domain)
                .where(Assessment14Domain.member_id == member_id)
                .order_by(Assessment14Domain.id.desc())
            )
        )

    def latest(self, member_id: int) -> Assessment14Domain | None:
        return self.db.scalar(
            select(Assessment14Domain)
            .where(Assessment14Domain.member_id == member_id)
            .order_by(Assessment14Domain.id.desc())
            .limit(1)
        )


class Jp7Repository:
    def __init__(self, db: Session):
        self.db = db

    def add(self, measurement: JacksonPollockMeasurement) -> JacksonPollockMeasurement:
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def history(self, member_id: int) -> list[JacksonPollockMeasurement]:
        return list(
            self.db.scalars(
                select(JacksonPollockMeasurement)
                .where(JacksonPollockMeasurement.member_id == member_id)
                .order_by(JacksonPollockMeasurement.id.desc())
            )
        )

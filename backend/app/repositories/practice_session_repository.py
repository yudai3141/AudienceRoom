from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession


class PracticeSessionRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, session: PracticeSession) -> PracticeSession:
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def get_by_id(self, session_id: int) -> PracticeSession | None:
        stmt = select(PracticeSession).where(
            PracticeSession.id == session_id,
            PracticeSession.deleted_at.is_(None),
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_user_id(self, user_id: int) -> list[PracticeSession]:
        stmt = (
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user_id,
                PracticeSession.deleted_at.is_(None),
            )
            .order_by(PracticeSession.created_at.desc())
        )
        return list(self._db.execute(stmt).scalars().all())

    def list_by_user_id_paginated(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> list[PracticeSession]:
        stmt = (
            select(PracticeSession)
            .where(
                PracticeSession.user_id == user_id,
                PracticeSession.deleted_at.is_(None),
            )
            .order_by(PracticeSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._db.execute(stmt).scalars().all())

    def count_by_user_id(self, user_id: int) -> int:
        stmt = select(func.count()).select_from(PracticeSession).where(
            PracticeSession.user_id == user_id,
            PracticeSession.deleted_at.is_(None),
        )
        return self._db.execute(stmt).scalar_one()

    def count_by_user_id_and_status(self, user_id: int, status: str) -> int:
        stmt = select(func.count()).select_from(PracticeSession).where(
            PracticeSession.user_id == user_id,
            PracticeSession.status == status,
            PracticeSession.deleted_at.is_(None),
        )
        return self._db.execute(stmt).scalar_one()

    def average_score_by_user_id(self, user_id: int) -> Decimal | None:
        stmt = select(func.avg(PracticeSession.overall_score)).where(
            PracticeSession.user_id == user_id,
            PracticeSession.overall_score.isnot(None),
            PracticeSession.deleted_at.is_(None),
        )
        return self._db.execute(stmt).scalar_one()

    def update(self, session: PracticeSession) -> PracticeSession:
        self._db.commit()
        self._db.refresh(session)
        return session

from sqlalchemy import select
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

    def update(self, session: PracticeSession) -> PracticeSession:
        self._db.commit()
        self._db.refresh(session)
        return session

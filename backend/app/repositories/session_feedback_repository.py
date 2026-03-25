from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.session_feedback import SessionFeedback


class SessionFeedbackRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, feedback: SessionFeedback) -> SessionFeedback:
        self._db.add(feedback)
        self._db.commit()
        self._db.refresh(feedback)
        return feedback

    def get_by_id(self, feedback_id: int) -> SessionFeedback | None:
        stmt = select(SessionFeedback).where(SessionFeedback.id == feedback_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_session_id(self, session_id: int) -> SessionFeedback | None:
        stmt = select(SessionFeedback).where(
            SessionFeedback.session_id == session_id
        )
        return self._db.execute(stmt).scalar_one_or_none()

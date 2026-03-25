from typing import Any

from sqlalchemy.orm import Session

from app.db.models.session_feedback import SessionFeedback
from app.repositories.session_feedback_repository import SessionFeedbackRepository


class SessionFeedbackService:
    def __init__(self, db: Session) -> None:
        self._repository = SessionFeedbackRepository(db)

    def create_feedback(
        self,
        session_id: int,
        user_id: int,
        summary_title: str,
        positive_points: Any,
        improvement_points: Any,
        short_comment: str | None = None,
        closing_message: str | None = None,
    ) -> SessionFeedback:
        existing = self._repository.get_by_session_id(session_id)
        if existing is not None:
            raise ValueError(
                f"Feedback for session {session_id} already exists"
            )

        feedback = SessionFeedback(
            session_id=session_id,
            user_id=user_id,
            summary_title=summary_title,
            positive_points=positive_points,
            improvement_points=improvement_points,
            short_comment=short_comment,
            closing_message=closing_message,
        )
        return self._repository.create(feedback)

    def get_feedback(self, feedback_id: int) -> SessionFeedback | None:
        return self._repository.get_by_id(feedback_id)

    def get_feedback_by_session(self, session_id: int) -> SessionFeedback | None:
        return self._repository.get_by_session_id(session_id)

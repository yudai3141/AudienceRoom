from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession, SESSION_STATUSES, SESSION_MODES
from app.repositories.practice_session_repository import PracticeSessionRepository


VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "waiting": {"active", "cancelled"},
    "active": {"completed", "cancelled", "error"},
    "completed": set(),
    "cancelled": set(),
    "error": set(),
}


class PracticeSessionService:
    def __init__(self, db: Session) -> None:
        self._repository = PracticeSessionRepository(db)

    def create_session(
        self,
        user_id: int,
        mode: str,
        participant_count: int,
        feedback_enabled: bool = True,
        theme: str | None = None,
        presentation_duration_sec: int | None = None,
        presentation_qa_count: int | None = None,
        user_goal: str | None = None,
        user_concerns: str | None = None,
        session_brief: str | None = None,
        target_context: str | None = None,
    ) -> PracticeSession:
        if mode not in SESSION_MODES:
            raise ValueError(f"Invalid mode '{mode}'. Must be one of {SESSION_MODES}")

        session = PracticeSession(
            user_id=user_id,
            mode=mode,
            participant_count=participant_count,
            feedback_enabled=feedback_enabled,
            theme=theme,
            presentation_duration_sec=presentation_duration_sec,
            presentation_qa_count=presentation_qa_count,
            user_goal=user_goal,
            user_concerns=user_concerns,
            session_brief=session_brief,
            target_context=target_context,
        )
        return self._repository.create(session)

    def get_session(self, session_id: int) -> PracticeSession | None:
        return self._repository.get_by_id(session_id)

    def list_user_sessions(self, user_id: int) -> list[PracticeSession]:
        return self._repository.list_by_user_id(user_id)

    def update_status(self, session_id: int, new_status: str) -> PracticeSession:
        if new_status not in SESSION_STATUSES:
            raise ValueError(
                f"Invalid status '{new_status}'. Must be one of {SESSION_STATUSES}"
            )

        session = self._repository.get_by_id(session_id)
        if session is None:
            raise ValueError(f"PracticeSession with id {session_id} not found")

        allowed = VALID_STATUS_TRANSITIONS.get(session.status, set())
        if new_status not in allowed:
            raise ValueError(
                f"Cannot transition from '{session.status}' to '{new_status}'"
            )

        session.status = new_status

        now = datetime.now(timezone.utc)
        if new_status == "active":
            session.started_at = now
        elif new_status in ("completed", "cancelled", "error"):
            session.ended_at = now

        return self._repository.update(session)

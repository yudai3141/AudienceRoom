from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession, SESSION_MODES, SESSION_STATUSES
from app.db.models.session_participant import SessionParticipant
from app.repositories.ai_character_repository import AiCharacterRepository
from app.repositories.feedback_metric_repository import FeedbackMetricRepository
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.session_feedback_repository import SessionFeedbackRepository
from app.repositories.session_message_repository import SessionMessageRepository
from app.repositories.session_participant_repository import SessionParticipantRepository
from app.schemas.feedback_metric import FeedbackMetricResponse
from app.schemas.practice_session import (
    DashboardResponse,
    PaginatedSessionListResponse,
    PracticeSessionDetailResponse,
    SessionFeedbackNested,
    SessionListItem,
    SessionMessageResponse,
    SessionParticipantResponse,
)
from app.schemas.ai_character import AiCharacterResponse


VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "waiting": {"active", "cancelled"},
    "active": {"completed", "cancelled", "error"},
    "completed": set(),
    "cancelled": set(),
    "error": set(),
}


class PracticeSessionService:
    def __init__(self, db: Session) -> None:
        self._db = db
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
        session = self._repository.create(session)

        self._assign_participants(session.id, participant_count)

        return session

    def _assign_participants(self, session_id: int, participant_count: int) -> None:
        character_repo = AiCharacterRepository(self._db)
        participant_repo = SessionParticipantRepository(self._db)

        characters = character_repo.list_active()
        if not characters:
            return

        assign_count = min(participant_count, len(characters))
        participants = []
        for i in range(assign_count):
            character = characters[i]
            role = "host" if i == 0 else "audience"
            display_name = f"面接官{i + 1}" if participant_count > 1 else "面接官"
            participants.append(
                SessionParticipant(
                    session_id=session_id,
                    ai_character_id=character.id,
                    display_name=display_name,
                    role=role,
                    seat_index=i,
                )
            )

        if participants:
            participant_repo.bulk_create(participants)

    def get_session(self, session_id: int) -> PracticeSession | None:
        return self._repository.get_by_id(session_id)

    def list_user_sessions(self, user_id: int) -> list[PracticeSession]:
        return self._repository.list_by_user_id(user_id)

    def list_user_sessions_paginated(
        self, user_id: int, *, limit: int = 20, offset: int = 0
    ) -> PaginatedSessionListResponse:
        rows = self._repository.list_by_user_id_with_feedback_flag(
            user_id, limit=limit, offset=offset
        )
        total = self._repository.count_by_user_id(user_id)

        items = [
            SessionListItem(
                id=row.session.id,
                status=row.session.status,
                mode=row.session.mode,
                theme=row.session.theme,
                overall_score=row.session.overall_score,
                has_feedback=row.has_feedback,
                started_at=row.session.started_at,
                ended_at=row.session.ended_at,
                created_at=row.session.created_at,
            )
            for row in rows
        ]

        return PaginatedSessionListResponse(
            items=items, total=total, limit=limit, offset=offset
        )

    def get_session_detail(self, session_id: int) -> PracticeSessionDetailResponse | None:
        session = self._repository.get_by_id(session_id)
        if session is None:
            return None

        participant_repo = SessionParticipantRepository(self._db)
        message_repo = SessionMessageRepository(self._db)
        feedback_repo = SessionFeedbackRepository(self._db)
        metric_repo = FeedbackMetricRepository(self._db)

        participants = participant_repo.list_by_session_id(session_id)
        messages = message_repo.list_by_session_id(session_id)
        feedback = feedback_repo.get_by_session_id(session_id)

        participant_responses = []
        for p in participants:
            pr = SessionParticipantResponse.model_validate(p)
            if p.ai_character:
                pr.ai_character = AiCharacterResponse.model_validate(p.ai_character)
            participant_responses.append(pr)

        feedback_nested = None
        if feedback is not None:
            metrics = metric_repo.list_by_feedback_id(feedback.id)
            feedback_nested = SessionFeedbackNested(
                id=feedback.id,
                summary_title=feedback.summary_title,
                short_comment=feedback.short_comment,
                positive_points=feedback.positive_points,
                improvement_points=feedback.improvement_points,
                closing_message=feedback.closing_message,
                created_at=feedback.created_at,
                metrics=[FeedbackMetricResponse.model_validate(m) for m in metrics],
            )

        return PracticeSessionDetailResponse(
            id=session.id,
            user_id=session.user_id,
            status=session.status,
            mode=session.mode,
            participant_count=session.participant_count,
            feedback_enabled=session.feedback_enabled,
            theme=session.theme,
            overall_score=session.overall_score,
            feedback_summary=session.feedback_summary,
            started_at=session.started_at,
            ended_at=session.ended_at,
            created_at=session.created_at,
            updated_at=session.updated_at,
            participants=participant_responses,
            messages=[SessionMessageResponse.model_validate(m) for m in messages],
            feedback=feedback_nested,
        )

    def get_dashboard(self, user_id: int) -> DashboardResponse:
        total = self._repository.count_by_user_id(user_id)
        completed = self._repository.count_by_user_id_and_status(user_id, "completed")
        avg_score = self._repository.average_score_by_user_id(user_id)

        recent_rows = self._repository.list_by_user_id_with_feedback_flag(
            user_id, limit=5, offset=0
        )
        recent_items = [
            SessionListItem(
                id=row.session.id,
                status=row.session.status,
                mode=row.session.mode,
                theme=row.session.theme,
                overall_score=row.session.overall_score,
                has_feedback=row.has_feedback,
                started_at=row.session.started_at,
                ended_at=row.session.ended_at,
                created_at=row.session.created_at,
            )
            for row in recent_rows
        ]

        return DashboardResponse(
            total_sessions=total,
            completed_sessions=completed,
            average_score=float(avg_score) if avg_score is not None else None,
            recent_sessions=recent_items,
        )

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

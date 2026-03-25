from sqlalchemy.orm import Session

from app.db.models.session_participant import SessionParticipant, PARTICIPANT_ROLES
from app.repositories.session_participant_repository import (
    SessionParticipantRepository,
)


class SessionParticipantService:
    def __init__(self, db: Session) -> None:
        self._repository = SessionParticipantRepository(db)

    def add_participant(
        self,
        session_id: int,
        ai_character_id: int,
        display_name: str,
        role: str,
        seat_index: int,
    ) -> SessionParticipant:
        if role not in PARTICIPANT_ROLES:
            raise ValueError(
                f"Invalid role '{role}'. Must be one of {PARTICIPANT_ROLES}"
            )

        participant = SessionParticipant(
            session_id=session_id,
            ai_character_id=ai_character_id,
            display_name=display_name,
            role=role,
            seat_index=seat_index,
        )
        return self._repository.create(participant)

    def add_participants_bulk(
        self,
        items: list[dict],
    ) -> list[SessionParticipant]:
        participants = []
        for item in items:
            if item["role"] not in PARTICIPANT_ROLES:
                raise ValueError(
                    f"Invalid role '{item['role']}'. Must be one of {PARTICIPANT_ROLES}"
                )
            participants.append(SessionParticipant(**item))
        return self._repository.bulk_create(participants)

    def get_participant(self, participant_id: int) -> SessionParticipant | None:
        return self._repository.get_by_id(participant_id)

    def list_session_participants(
        self, session_id: int
    ) -> list[SessionParticipant]:
        return self._repository.list_by_session_id(session_id)

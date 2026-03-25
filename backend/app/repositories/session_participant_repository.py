from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.session_participant import SessionParticipant


class SessionParticipantRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, participant: SessionParticipant) -> SessionParticipant:
        self._db.add(participant)
        self._db.commit()
        self._db.refresh(participant)
        return participant

    def bulk_create(
        self, participants: list[SessionParticipant]
    ) -> list[SessionParticipant]:
        self._db.add_all(participants)
        self._db.commit()
        for p in participants:
            self._db.refresh(p)
        return participants

    def get_by_id(self, participant_id: int) -> SessionParticipant | None:
        stmt = select(SessionParticipant).where(
            SessionParticipant.id == participant_id
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_session_id(self, session_id: int) -> list[SessionParticipant]:
        stmt = (
            select(SessionParticipant)
            .where(SessionParticipant.session_id == session_id)
            .order_by(SessionParticipant.seat_index)
        )
        return list(self._db.execute(stmt).scalars().all())

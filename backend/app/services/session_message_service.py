from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.session_message import SessionMessage
from app.repositories.session_message_repository import SessionMessageRepository


class SessionMessageService:
    def __init__(self, db: Session) -> None:
        self._repository = SessionMessageRepository(db)

    def add_message(
        self,
        session_id: int,
        sequence_no: int,
        content: str,
        participant_id: int | None = None,
        transcript_confidence: Decimal | None = None,
    ) -> SessionMessage:
        message = SessionMessage(
            session_id=session_id,
            participant_id=participant_id,
            sequence_no=sequence_no,
            content=content,
            transcript_confidence=transcript_confidence,
        )
        return self._repository.create(message)

    def get_message(self, message_id: int) -> SessionMessage | None:
        return self._repository.get_by_id(message_id)

    def list_session_messages(self, session_id: int) -> list[SessionMessage]:
        return self._repository.list_by_session_id(session_id)

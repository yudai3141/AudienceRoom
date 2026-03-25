from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.session_message import SessionMessage


class SessionMessageRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, message: SessionMessage) -> SessionMessage:
        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)
        return message

    def get_by_id(self, message_id: int) -> SessionMessage | None:
        stmt = select(SessionMessage).where(SessionMessage.id == message_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_session_id(self, session_id: int) -> list[SessionMessage]:
        stmt = (
            select(SessionMessage)
            .where(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.sequence_no)
        )
        return list(self._db.execute(stmt).scalars().all())

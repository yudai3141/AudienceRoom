from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.user import User
from app.services.session_message_service import SessionMessageService


def _setup(db: Session) -> int:
    user = User(
        firebase_uid="sm_svc_user", email="sm_svc@example.com",
        display_name="SM Svc User",
    )
    db.add(user)
    db.flush()
    session = PracticeSession(
        user_id=user.id, mode="presentation", participant_count=3,
    )
    db.add(session)
    db.flush()
    return session.id


class TestSessionMessageService:
    def test_add_message(self, db: Session) -> None:
        session_id = _setup(db)
        service = SessionMessageService(db)
        msg = service.add_message(
            session_id=session_id, sequence_no=1, content="サービステスト",
        )
        assert msg.id is not None
        assert msg.content == "サービステスト"

    def test_add_message_with_confidence(self, db: Session) -> None:
        session_id = _setup(db)
        service = SessionMessageService(db)
        msg = service.add_message(
            session_id=session_id, sequence_no=1, content="信頼度付き",
            transcript_confidence=Decimal("0.880"),
        )
        assert msg.transcript_confidence == Decimal("0.880")

    def test_get_message(self, db: Session) -> None:
        session_id = _setup(db)
        service = SessionMessageService(db)
        created = service.add_message(
            session_id=session_id, sequence_no=1, content="取得テスト",
        )
        found = service.get_message(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_message_not_found(self, db: Session) -> None:
        service = SessionMessageService(db)
        assert service.get_message(99999) is None

    def test_list_session_messages(self, db: Session) -> None:
        session_id = _setup(db)
        service = SessionMessageService(db)
        service.add_message(session_id=session_id, sequence_no=1, content="1つ目")
        service.add_message(session_id=session_id, sequence_no=2, content="2つ目")

        messages = service.list_session_messages(session_id)
        assert len(messages) == 2
        assert [m.sequence_no for m in messages] == [1, 2]

from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.session_message import SessionMessage
from app.db.models.user import User
from app.repositories.session_message_repository import SessionMessageRepository


def _setup(db: Session) -> int:
    user = User(
        firebase_uid="sm_repo_user", email="sm_repo@example.com",
        display_name="SM Repo User",
    )
    db.add(user)
    db.flush()
    session = PracticeSession(
        user_id=user.id, mode="interview", participant_count=2,
    )
    db.add(session)
    db.flush()
    return session.id


class TestSessionMessageRepository:
    def test_create(self, db: Session) -> None:
        session_id = _setup(db)
        repo = SessionMessageRepository(db)
        msg = SessionMessage(
            session_id=session_id, sequence_no=1, content="こんにちは",
        )
        created = repo.create(msg)
        assert created.id is not None
        assert created.content == "こんにちは"

    def test_create_with_confidence(self, db: Session) -> None:
        session_id = _setup(db)
        repo = SessionMessageRepository(db)
        msg = SessionMessage(
            session_id=session_id, sequence_no=1, content="テスト",
            transcript_confidence=Decimal("0.950"),
        )
        created = repo.create(msg)
        assert created.transcript_confidence == Decimal("0.950")

    def test_get_by_id(self, db: Session) -> None:
        session_id = _setup(db)
        repo = SessionMessageRepository(db)
        created = repo.create(SessionMessage(
            session_id=session_id, sequence_no=1, content="取得テスト",
        ))
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, db: Session) -> None:
        repo = SessionMessageRepository(db)
        assert repo.get_by_id(99999) is None

    def test_list_by_session_id_ordered(self, db: Session) -> None:
        session_id = _setup(db)
        repo = SessionMessageRepository(db)
        repo.create(SessionMessage(
            session_id=session_id, sequence_no=2, content="2番目",
        ))
        repo.create(SessionMessage(
            session_id=session_id, sequence_no=1, content="1番目",
        ))
        repo.create(SessionMessage(
            session_id=session_id, sequence_no=3, content="3番目",
        ))

        messages = repo.list_by_session_id(session_id)
        assert len(messages) == 3
        assert [m.sequence_no for m in messages] == [1, 2, 3]

    def test_list_by_session_id_empty(self, db: Session) -> None:
        repo = SessionMessageRepository(db)
        assert repo.list_by_session_id(99999) == []

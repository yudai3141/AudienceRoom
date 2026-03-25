from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.user import User
from app.repositories.practice_session_repository import PracticeSessionRepository


def _create_user(db: Session) -> User:
    user = User(
        firebase_uid="ps_repo_user",
        email="ps_repo@example.com",
        display_name="PS Repo User",
    )
    db.add(user)
    db.flush()
    return user


class TestPracticeSessionRepository:
    def test_create(self, db: Session) -> None:
        user = _create_user(db)
        repo = PracticeSessionRepository(db)
        session = PracticeSession(
            user_id=user.id,
            mode="interview",
            participant_count=3,
        )
        created = repo.create(session)

        assert created.id is not None
        assert created.user_id == user.id
        assert created.status == "waiting"
        assert created.mode == "interview"
        assert created.participant_count == 3
        assert created.feedback_enabled is True

    def test_get_by_id(self, db: Session) -> None:
        user = _create_user(db)
        repo = PracticeSessionRepository(db)
        session = PracticeSession(
            user_id=user.id, mode="presentation", participant_count=5,
        )
        created = repo.create(session)

        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, db: Session) -> None:
        repo = PracticeSessionRepository(db)
        assert repo.get_by_id(99999) is None

    def test_list_by_user_id(self, db: Session) -> None:
        user = _create_user(db)
        repo = PracticeSessionRepository(db)
        repo.create(PracticeSession(
            user_id=user.id, mode="interview", participant_count=2,
        ))
        repo.create(PracticeSession(
            user_id=user.id, mode="presentation", participant_count=4,
        ))

        sessions = repo.list_by_user_id(user.id)
        assert len(sessions) == 2

    def test_list_by_user_id_empty(self, db: Session) -> None:
        repo = PracticeSessionRepository(db)
        sessions = repo.list_by_user_id(99999)
        assert sessions == []

    def test_update(self, db: Session) -> None:
        user = _create_user(db)
        repo = PracticeSessionRepository(db)
        session = PracticeSession(
            user_id=user.id, mode="free_conversation", participant_count=1,
        )
        created = repo.create(session)

        created.status = "active"
        updated = repo.update(created)
        assert updated.status == "active"

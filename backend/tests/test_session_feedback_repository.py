from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.session_feedback import SessionFeedback
from app.db.models.user import User
from app.repositories.session_feedback_repository import SessionFeedbackRepository


def _setup(db: Session) -> tuple[int, int]:
    user = User(
        firebase_uid="sf_repo_user", email="sf_repo@example.com",
        display_name="SF Repo User",
    )
    db.add(user)
    db.flush()
    session = PracticeSession(
        user_id=user.id, mode="interview", participant_count=3,
    )
    db.add(session)
    db.flush()
    return session.id, user.id


class TestSessionFeedbackRepository:
    def test_create(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        repo = SessionFeedbackRepository(db)
        feedback = SessionFeedback(
            session_id=session_id, user_id=user_id,
            summary_title="よくできました",
            positive_points=["声が大きい", "論理的"],
            improvement_points=["もう少しゆっくり"],
        )
        created = repo.create(feedback)
        assert created.id is not None
        assert created.positive_points == ["声が大きい", "論理的"]

    def test_get_by_id(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        repo = SessionFeedbackRepository(db)
        created = repo.create(SessionFeedback(
            session_id=session_id, user_id=user_id,
            summary_title="テスト", positive_points=[], improvement_points=[],
        ))
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, db: Session) -> None:
        repo = SessionFeedbackRepository(db)
        assert repo.get_by_id(99999) is None

    def test_get_by_session_id(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        repo = SessionFeedbackRepository(db)
        repo.create(SessionFeedback(
            session_id=session_id, user_id=user_id,
            summary_title="セッション別取得",
            positive_points=["良い"], improvement_points=["改善"],
        ))
        found = repo.get_by_session_id(session_id)
        assert found is not None
        assert found.session_id == session_id

    def test_get_by_session_id_not_found(self, db: Session) -> None:
        repo = SessionFeedbackRepository(db)
        assert repo.get_by_session_id(99999) is None

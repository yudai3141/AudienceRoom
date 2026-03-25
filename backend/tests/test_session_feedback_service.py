import pytest
from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.user import User
from app.services.session_feedback_service import SessionFeedbackService


def _setup(db: Session) -> tuple[int, int]:
    user = User(
        firebase_uid="sf_svc_user", email="sf_svc@example.com",
        display_name="SF Svc User",
    )
    db.add(user)
    db.flush()
    session = PracticeSession(
        user_id=user.id, mode="presentation", participant_count=5,
    )
    db.add(session)
    db.flush()
    return session.id, user.id


class TestSessionFeedbackService:
    def test_create_feedback(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        service = SessionFeedbackService(db)
        feedback = service.create_feedback(
            session_id=session_id, user_id=user_id,
            summary_title="全体的に良い",
            positive_points=["堂々としていた"],
            improvement_points=["結論を先に"],
            short_comment="お疲れ様でした",
        )
        assert feedback.id is not None
        assert feedback.summary_title == "全体的に良い"

    def test_create_feedback_duplicate(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        service = SessionFeedbackService(db)
        service.create_feedback(
            session_id=session_id, user_id=user_id,
            summary_title="1回目", positive_points=[], improvement_points=[],
        )
        with pytest.raises(ValueError, match="already exists"):
            service.create_feedback(
                session_id=session_id, user_id=user_id,
                summary_title="2回目", positive_points=[], improvement_points=[],
            )

    def test_get_feedback(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        service = SessionFeedbackService(db)
        created = service.create_feedback(
            session_id=session_id, user_id=user_id,
            summary_title="取得テスト", positive_points=[], improvement_points=[],
        )
        found = service.get_feedback(created.id)
        assert found is not None

    def test_get_feedback_not_found(self, db: Session) -> None:
        service = SessionFeedbackService(db)
        assert service.get_feedback(99999) is None

    def test_get_feedback_by_session(self, db: Session) -> None:
        session_id, user_id = _setup(db)
        service = SessionFeedbackService(db)
        service.create_feedback(
            session_id=session_id, user_id=user_id,
            summary_title="セッション別", positive_points=[], improvement_points=[],
        )
        found = service.get_feedback_by_session(session_id)
        assert found is not None
        assert found.session_id == session_id

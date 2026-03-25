from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.feedback_metric import FeedbackMetric
from app.db.models.practice_session import PracticeSession
from app.db.models.session_feedback import SessionFeedback
from app.db.models.user import User
from app.repositories.feedback_metric_repository import FeedbackMetricRepository


def _setup(db: Session) -> int:
    user = User(
        firebase_uid="fm_repo_user", email="fm_repo@example.com",
        display_name="FM Repo User",
    )
    db.add(user)
    db.flush()
    session = PracticeSession(
        user_id=user.id, mode="interview", participant_count=3,
    )
    db.add(session)
    db.flush()
    feedback = SessionFeedback(
        session_id=session.id, user_id=user.id,
        summary_title="テスト", positive_points=[], improvement_points=[],
    )
    db.add(feedback)
    db.flush()
    return feedback.id


class TestFeedbackMetricRepository:
    def test_create(self, db: Session) -> None:
        feedback_id = _setup(db)
        repo = FeedbackMetricRepository(db)
        metric = FeedbackMetric(
            feedback_id=feedback_id, metric_key="clarity",
            metric_value=Decimal("85.50"), metric_label="明瞭さ", metric_unit="点",
        )
        created = repo.create(metric)
        assert created.id is not None
        assert created.metric_value == Decimal("85.50")

    def test_bulk_create(self, db: Session) -> None:
        feedback_id = _setup(db)
        repo = FeedbackMetricRepository(db)
        metrics = [
            FeedbackMetric(
                feedback_id=feedback_id, metric_key="speed",
                metric_value=Decimal("70.00"),
            ),
            FeedbackMetric(
                feedback_id=feedback_id, metric_key="volume",
                metric_value=Decimal("90.00"),
            ),
        ]
        created = repo.bulk_create(metrics)
        assert len(created) == 2

    def test_get_by_id(self, db: Session) -> None:
        feedback_id = _setup(db)
        repo = FeedbackMetricRepository(db)
        created = repo.create(FeedbackMetric(
            feedback_id=feedback_id, metric_key="test",
            metric_value=Decimal("50.00"),
        ))
        found = repo.get_by_id(created.id)
        assert found is not None

    def test_get_by_id_not_found(self, db: Session) -> None:
        repo = FeedbackMetricRepository(db)
        assert repo.get_by_id(99999) is None

    def test_list_by_feedback_id(self, db: Session) -> None:
        feedback_id = _setup(db)
        repo = FeedbackMetricRepository(db)
        repo.create(FeedbackMetric(
            feedback_id=feedback_id, metric_key="a", metric_value=Decimal("1.00"),
        ))
        repo.create(FeedbackMetric(
            feedback_id=feedback_id, metric_key="b", metric_value=Decimal("2.00"),
        ))
        metrics = repo.list_by_feedback_id(feedback_id)
        assert len(metrics) == 2

    def test_list_by_feedback_id_empty(self, db: Session) -> None:
        repo = FeedbackMetricRepository(db)
        assert repo.list_by_feedback_id(99999) == []

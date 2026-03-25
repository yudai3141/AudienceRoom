from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.session_feedback import SessionFeedback
from app.db.models.user import User
from app.services.feedback_metric_service import FeedbackMetricService


def _setup(db: Session) -> int:
    user = User(
        firebase_uid="fm_svc_user", email="fm_svc@example.com",
        display_name="FM Svc User",
    )
    db.add(user)
    db.flush()
    session = PracticeSession(
        user_id=user.id, mode="presentation", participant_count=5,
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


class TestFeedbackMetricService:
    def test_add_metric(self, db: Session) -> None:
        feedback_id = _setup(db)
        service = FeedbackMetricService(db)
        metric = service.add_metric(
            feedback_id=feedback_id, metric_key="clarity",
            metric_value=Decimal("85.50"), metric_label="明瞭さ", metric_unit="点",
        )
        assert metric.id is not None
        assert metric.metric_key == "clarity"

    def test_add_metrics_bulk(self, db: Session) -> None:
        feedback_id = _setup(db)
        service = FeedbackMetricService(db)
        items = [
            {"feedback_id": feedback_id, "metric_key": "speed", "metric_value": Decimal("70.00")},
            {"feedback_id": feedback_id, "metric_key": "volume", "metric_value": Decimal("90.00")},
        ]
        created = service.add_metrics_bulk(items)
        assert len(created) == 2

    def test_get_metric(self, db: Session) -> None:
        feedback_id = _setup(db)
        service = FeedbackMetricService(db)
        created = service.add_metric(
            feedback_id=feedback_id, metric_key="test",
            metric_value=Decimal("50.00"),
        )
        found = service.get_metric(created.id)
        assert found is not None

    def test_get_metric_not_found(self, db: Session) -> None:
        service = FeedbackMetricService(db)
        assert service.get_metric(99999) is None

    def test_list_feedback_metrics(self, db: Session) -> None:
        feedback_id = _setup(db)
        service = FeedbackMetricService(db)
        service.add_metric(
            feedback_id=feedback_id, metric_key="a", metric_value=Decimal("1.00"),
        )
        service.add_metric(
            feedback_id=feedback_id, metric_key="b", metric_value=Decimal("2.00"),
        )
        metrics = service.list_feedback_metrics(feedback_id)
        assert len(metrics) == 2

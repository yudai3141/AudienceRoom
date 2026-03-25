from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.feedback_metric import FeedbackMetric


class FeedbackMetricRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, metric: FeedbackMetric) -> FeedbackMetric:
        self._db.add(metric)
        self._db.commit()
        self._db.refresh(metric)
        return metric

    def bulk_create(self, metrics: list[FeedbackMetric]) -> list[FeedbackMetric]:
        self._db.add_all(metrics)
        self._db.commit()
        for m in metrics:
            self._db.refresh(m)
        return metrics

    def get_by_id(self, metric_id: int) -> FeedbackMetric | None:
        stmt = select(FeedbackMetric).where(FeedbackMetric.id == metric_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_feedback_id(self, feedback_id: int) -> list[FeedbackMetric]:
        stmt = (
            select(FeedbackMetric)
            .where(FeedbackMetric.feedback_id == feedback_id)
            .order_by(FeedbackMetric.id)
        )
        return list(self._db.execute(stmt).scalars().all())

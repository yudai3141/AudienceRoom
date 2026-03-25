from decimal import Decimal

from sqlalchemy.orm import Session

from app.db.models.feedback_metric import FeedbackMetric
from app.repositories.feedback_metric_repository import FeedbackMetricRepository


class FeedbackMetricService:
    def __init__(self, db: Session) -> None:
        self._repository = FeedbackMetricRepository(db)

    def add_metric(
        self,
        feedback_id: int,
        metric_key: str,
        metric_value: Decimal,
        metric_label: str | None = None,
        metric_unit: str | None = None,
    ) -> FeedbackMetric:
        metric = FeedbackMetric(
            feedback_id=feedback_id,
            metric_key=metric_key,
            metric_value=metric_value,
            metric_label=metric_label,
            metric_unit=metric_unit,
        )
        return self._repository.create(metric)

    def add_metrics_bulk(self, items: list[dict]) -> list[FeedbackMetric]:
        metrics = [FeedbackMetric(**item) for item in items]
        return self._repository.bulk_create(metrics)

    def get_metric(self, metric_id: int) -> FeedbackMetric | None:
        return self._repository.get_by_id(metric_id)

    def list_feedback_metrics(self, feedback_id: int) -> list[FeedbackMetric]:
        return self._repository.list_by_feedback_id(feedback_id)

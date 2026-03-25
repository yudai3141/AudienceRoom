from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FeedbackMetricCreateRequest(BaseModel):
    feedback_id: int
    metric_key: str
    metric_value: Decimal
    metric_label: str | None = None
    metric_unit: str | None = None


class FeedbackMetricBulkCreateRequest(BaseModel):
    metrics: list[FeedbackMetricCreateRequest]


class FeedbackMetricResponse(BaseModel):
    id: int
    feedback_id: int
    metric_key: str
    metric_value: Decimal
    metric_label: str | None
    metric_unit: str | None
    created_at: datetime

    model_config = {"from_attributes": True}

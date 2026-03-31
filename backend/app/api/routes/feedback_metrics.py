from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.feedback_metric import (
    FeedbackMetricBulkCreateRequest,
    FeedbackMetricCreateRequest,
    FeedbackMetricResponse,
)
from app.services.feedback_metric_service import FeedbackMetricService

router = APIRouter(prefix="/feedback-metrics", tags=["feedback-metrics"])


@router.post(
    "", response_model=FeedbackMetricResponse, status_code=201
)
def create_feedback_metric(
    body: FeedbackMetricCreateRequest,
    db: Session = Depends(get_db),
) -> FeedbackMetricResponse:
    service = FeedbackMetricService(db)
    metric = service.add_metric(
        feedback_id=body.feedback_id,
        metric_key=body.metric_key,
        metric_value=body.metric_value,
        metric_label=body.metric_label,
        metric_unit=body.metric_unit,
    )
    return FeedbackMetricResponse.model_validate(metric)


@router.post(
    "/bulk",
    response_model=list[FeedbackMetricResponse],
    status_code=201,
)
def create_feedback_metrics_bulk(
    body: FeedbackMetricBulkCreateRequest,
    db: Session = Depends(get_db),
) -> list[FeedbackMetricResponse]:
    service = FeedbackMetricService(db)
    metrics = service.add_metrics_bulk([m.model_dump() for m in body.metrics])
    return [FeedbackMetricResponse.model_validate(m) for m in metrics]


@router.get("", response_model=list[FeedbackMetricResponse])
def list_feedback_metrics(
    feedback_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[FeedbackMetricResponse]:
    service = FeedbackMetricService(db)
    metrics = service.list_feedback_metrics(feedback_id)
    return [FeedbackMetricResponse.model_validate(m) for m in metrics]


@router.get(
    "/{metric_id}", response_model=FeedbackMetricResponse
)
def get_feedback_metric(
    metric_id: int,
    db: Session = Depends(get_db),
) -> FeedbackMetricResponse:
    service = FeedbackMetricService(db)
    metric = service.get_metric(metric_id)
    if metric is None:
        raise HTTPException(status_code=404, detail="FeedbackMetric not found")
    return FeedbackMetricResponse.model_validate(metric)

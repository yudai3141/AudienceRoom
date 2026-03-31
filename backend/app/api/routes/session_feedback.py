from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.session_feedback import (
    SessionFeedbackCreateRequest,
    SessionFeedbackResponse,
)
from app.services.session_feedback_service import SessionFeedbackService

router = APIRouter(prefix="/session-feedback", tags=["session-feedback"])


@router.post(
    "", response_model=SessionFeedbackResponse, status_code=201
)
def create_session_feedback(
    body: SessionFeedbackCreateRequest,
    db: Session = Depends(get_db),
) -> SessionFeedbackResponse:
    service = SessionFeedbackService(db)
    try:
        feedback = service.create_feedback(
            session_id=body.session_id,
            user_id=body.user_id,
            summary_title=body.summary_title,
            positive_points=body.positive_points,
            improvement_points=body.improvement_points,
            short_comment=body.short_comment,
            closing_message=body.closing_message,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return SessionFeedbackResponse.model_validate(feedback)


@router.get(
    "/{feedback_id}", response_model=SessionFeedbackResponse
)
def get_session_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
) -> SessionFeedbackResponse:
    service = SessionFeedbackService(db)
    feedback = service.get_feedback(feedback_id)
    if feedback is None:
        raise HTTPException(status_code=404, detail="SessionFeedback not found")
    return SessionFeedbackResponse.model_validate(feedback)


@router.get(
    "", response_model=SessionFeedbackResponse
)
def get_session_feedback_by_session(
    session_id: int = Query(...),
    db: Session = Depends(get_db),
) -> SessionFeedbackResponse:
    service = SessionFeedbackService(db)
    feedback = service.get_feedback_by_session(session_id)
    if feedback is None:
        raise HTTPException(status_code=404, detail="SessionFeedback not found")
    return SessionFeedbackResponse.model_validate(feedback)

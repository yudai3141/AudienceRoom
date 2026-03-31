from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.practice_session import (
    FeedbackGenerationResponse,
    PaginatedSessionListResponse,
    PracticeSessionCreateRequest,
    PracticeSessionDetailResponse,
    PracticeSessionResponse,
    PracticeSessionStatusUpdateRequest,
)
from app.services.ai.feedback_generator import FeedbackGenerator
from app.services.practice_session_service import PracticeSessionService

router = APIRouter(prefix="/practice-sessions", tags=["practice-sessions"])


@router.post("", response_model=PracticeSessionResponse, status_code=201)
def create_practice_session(
    body: PracticeSessionCreateRequest,
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    service = PracticeSessionService(db)
    try:
        session = service.create_session(
            user_id=body.user_id,
            mode=body.mode,
            participant_count=body.participant_count,
            feedback_enabled=body.feedback_enabled,
            theme=body.theme,
            presentation_duration_sec=body.presentation_duration_sec,
            presentation_qa_count=body.presentation_qa_count,
            user_goal=body.user_goal,
            user_concerns=body.user_concerns,
            session_brief=body.session_brief,
            target_context=body.target_context,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PracticeSessionResponse.model_validate(session)


@router.get("", response_model=PaginatedSessionListResponse)
def list_practice_sessions(
    user_id: int = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedSessionListResponse:
    service = PracticeSessionService(db)
    return service.list_user_sessions_paginated(user_id, limit=limit, offset=offset)


@router.get(
    "/{session_id}/detail",
    response_model=PracticeSessionDetailResponse,
)
def get_practice_session_detail(
    session_id: int,
    db: Session = Depends(get_db),
) -> PracticeSessionDetailResponse:
    service = PracticeSessionService(db)
    detail = service.get_session_detail(session_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="PracticeSession not found")
    return detail


@router.get(
    "/{session_id}", response_model=PracticeSessionResponse
)
def get_practice_session(
    session_id: int,
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    service = PracticeSessionService(db)
    session = service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="PracticeSession not found")
    return PracticeSessionResponse.model_validate(session)


@router.patch(
    "/{session_id}/status",
    response_model=PracticeSessionResponse,
)
def update_practice_session_status(
    session_id: int,
    body: PracticeSessionStatusUpdateRequest,
    db: Session = Depends(get_db),
) -> PracticeSessionResponse:
    service = PracticeSessionService(db)
    try:
        session = service.update_status(session_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return PracticeSessionResponse.model_validate(session)


@router.post(
    "/{session_id}/generate-feedback",
    response_model=FeedbackGenerationResponse,
)
async def generate_feedback(
    session_id: int,
    db: Session = Depends(get_db),
) -> FeedbackGenerationResponse:
    """Generate AI feedback for a completed practice session."""
    generator = FeedbackGenerator(db)
    try:
        result = await generator.generate_feedback(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return FeedbackGenerationResponse(
        session_id=session_id,
        feedback_id=result.feedback.id,
        overall_score=result.overall_score,
        summary_title=result.feedback.summary_title,
        short_comment=result.feedback.short_comment,
    )

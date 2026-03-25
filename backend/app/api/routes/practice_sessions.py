from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.practice_session import (
    DashboardResponse,
    PaginatedSessionListResponse,
    PracticeSessionCreateRequest,
    PracticeSessionDetailResponse,
    PracticeSessionResponse,
    PracticeSessionStatusUpdateRequest,
)
from app.services.practice_session_service import PracticeSessionService

router = APIRouter()


@router.post(
    "/practice-sessions", response_model=PracticeSessionResponse, status_code=201
)
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


@router.get("/practice-sessions", response_model=PaginatedSessionListResponse)
def list_practice_sessions(
    user_id: int = Query(...),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> PaginatedSessionListResponse:
    service = PracticeSessionService(db)
    return service.list_user_sessions_paginated(user_id, limit=limit, offset=offset)


@router.get(
    "/practice-sessions/{session_id}/detail",
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
    "/practice-sessions/{session_id}", response_model=PracticeSessionResponse
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
    "/practice-sessions/{session_id}/status",
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


@router.get("/users/me/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    service = PracticeSessionService(db)
    return service.get_dashboard(current_user.id)

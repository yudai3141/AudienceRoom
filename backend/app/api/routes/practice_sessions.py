from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.practice_session import (
    PracticeSessionCreateRequest,
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


@router.get("/practice-sessions", response_model=list[PracticeSessionResponse])
def list_practice_sessions(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[PracticeSessionResponse]:
    service = PracticeSessionService(db)
    sessions = service.list_user_sessions(user_id)
    return [PracticeSessionResponse.model_validate(s) for s in sessions]


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

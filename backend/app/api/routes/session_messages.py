from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.session_message import (
    SessionMessageCreateRequest,
    SessionMessageResponse,
)
from app.services.session_message_service import SessionMessageService

router = APIRouter()


@router.post(
    "/session-messages", response_model=SessionMessageResponse, status_code=201
)
def create_session_message(
    body: SessionMessageCreateRequest,
    db: Session = Depends(get_db),
) -> SessionMessageResponse:
    service = SessionMessageService(db)
    message = service.add_message(
        session_id=body.session_id,
        participant_id=body.participant_id,
        sequence_no=body.sequence_no,
        content=body.content,
        transcript_confidence=body.transcript_confidence,
    )
    return SessionMessageResponse.model_validate(message)


@router.get("/session-messages", response_model=list[SessionMessageResponse])
def list_session_messages(
    session_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[SessionMessageResponse]:
    service = SessionMessageService(db)
    messages = service.list_session_messages(session_id)
    return [SessionMessageResponse.model_validate(m) for m in messages]


@router.get(
    "/session-messages/{message_id}", response_model=SessionMessageResponse
)
def get_session_message(
    message_id: int,
    db: Session = Depends(get_db),
) -> SessionMessageResponse:
    service = SessionMessageService(db)
    message = service.get_message(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="SessionMessage not found")
    return SessionMessageResponse.model_validate(message)

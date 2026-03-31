from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.session_participant import (
    SessionParticipantBulkCreateRequest,
    SessionParticipantCreateRequest,
    SessionParticipantResponse,
)
from app.services.session_participant_service import SessionParticipantService

router = APIRouter(prefix="/session-participants", tags=["session-participants"])


@router.post(
    "",
    response_model=SessionParticipantResponse,
    status_code=201,
)
def create_session_participant(
    body: SessionParticipantCreateRequest,
    db: Session = Depends(get_db),
) -> SessionParticipantResponse:
    service = SessionParticipantService(db)
    try:
        participant = service.add_participant(
            session_id=body.session_id,
            ai_character_id=body.ai_character_id,
            display_name=body.display_name,
            role=body.role,
            seat_index=body.seat_index,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return SessionParticipantResponse.model_validate(participant)


@router.post(
    "/bulk",
    response_model=list[SessionParticipantResponse],
    status_code=201,
)
def create_session_participants_bulk(
    body: SessionParticipantBulkCreateRequest,
    db: Session = Depends(get_db),
) -> list[SessionParticipantResponse]:
    service = SessionParticipantService(db)
    try:
        participants = service.add_participants_bulk(
            [p.model_dump() for p in body.participants]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return [SessionParticipantResponse.model_validate(p) for p in participants]


@router.get(
    "",
    response_model=list[SessionParticipantResponse],
)
def list_session_participants(
    session_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[SessionParticipantResponse]:
    service = SessionParticipantService(db)
    participants = service.list_session_participants(session_id)
    return [SessionParticipantResponse.model_validate(p) for p in participants]


@router.get(
    "/{participant_id}",
    response_model=SessionParticipantResponse,
)
def get_session_participant(
    participant_id: int,
    db: Session = Depends(get_db),
) -> SessionParticipantResponse:
    service = SessionParticipantService(db)
    participant = service.get_participant(participant_id)
    if participant is None:
        raise HTTPException(status_code=404, detail="SessionParticipant not found")
    return SessionParticipantResponse.model_validate(participant)

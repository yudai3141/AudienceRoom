from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ai.conversation_service import ConversationService

router = APIRouter()


class ConversationMessageRequest(BaseModel):
    session_id: int
    message: str
    generate_audio: bool = True


class ConversationStartRequest(BaseModel):
    session_id: int
    generate_audio: bool = True


class ConversationResponse(BaseModel):
    text: str
    audio_base64: str | None = None
    speaker_id: int | None = None
    participant_id: int | None = None


@router.post("/conversation/message", response_model=ConversationResponse)
async def send_message(
    body: ConversationMessageRequest,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Send a message to the AI and receive a response.

    This endpoint processes the user's spoken message, generates an AI response
    using the appropriate prompt for the session mode, and optionally returns
    synthesized audio using VOICEVOX.
    """
    service = ConversationService(db)
    try:
        result = await service.process_message(
            session_id=body.session_id,
            user_message=body.message,
            generate_audio=body.generate_audio,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ConversationResponse(
        text=result.text,
        audio_base64=result.audio_base64,
        speaker_id=result.speaker_id,
        participant_id=result.participant_id,
    )


@router.post("/conversation/start", response_model=ConversationResponse)
async def start_conversation(
    body: ConversationStartRequest,
    db: Session = Depends(get_db),
) -> ConversationResponse:
    """Start a conversation and get the AI's opening message.

    This endpoint generates the AI's initial greeting or prompt based on
    the session mode and settings.
    """
    service = ConversationService(db)
    try:
        result = await service.start_conversation(
            session_id=body.session_id,
            generate_audio=body.generate_audio,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return ConversationResponse(
        text=result.text,
        audio_base64=result.audio_base64,
        speaker_id=result.speaker_id,
        participant_id=result.participant_id,
    )

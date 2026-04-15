import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.conversation import (
    ConversationMessageRequest,
    ConversationResponse,
    ConversationStartRequest,
)
from app.services.ai.conversation_service import ConversationService
from app.services.ai.streaming_conversation_service import StreamingConversationService

router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/message", response_model=ConversationResponse)
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


@router.post("/start", response_model=ConversationResponse)
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


@router.post("/message/stream")
async def send_message_stream(
    body: ConversationMessageRequest,
    db: Session = Depends(get_db),
):
    """メッセージを送信し、Server-Sent Events経由でストリーミングレスポンスを受信する

    このエンドポイントはユーザーのメッセージを処理し、AI応答を
    リアルタイムでストリーミング配信します（増分テキストと音声チャンクを含む）

    Server-Sent Events (SSE)を返す:
    - event: metadata, data: {participant_id, speaker_id}
    - event: text_chunk, data: {text}
    - event: audio_chunk, data: {audio_base64, sequence, text}
    - event: complete, data: {text, audio_sequence_count}
    - event: error, data: {message}
    """
    service = StreamingConversationService(db)

    async def event_generator():
        async for event in service.process_message_stream(
            session_id=body.session_id,
            user_message=body.message,
            generate_audio=body.generate_audio,
        ):
            yield f"event: {event.event_type}\n"
            yield f"data: {json.dumps(event.data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/start/stream")
async def start_conversation_stream(
    body: ConversationStartRequest,
    db: Session = Depends(get_db),
):
    """会話を開始し、AIの開始メッセージをSSE経由でストリーミング配信する

    Server-Sent Events (SSE)を返す:
    - event: metadata, data: {participant_id, speaker_id}
    - event: text_chunk, data: {text}
    - event: audio_chunk, data: {audio_base64, sequence, text}
    - event: complete, data: {text, audio_sequence_count}
    - event: error, data: {message}
    """
    service = StreamingConversationService(db)

    async def event_generator():
        async for event in service.start_conversation_stream(
            session_id=body.session_id,
            generate_audio=body.generate_audio,
        ):
            yield f"event: {event.event_type}\n"
            yield f"data: {json.dumps(event.data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

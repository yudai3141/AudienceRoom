from pydantic import BaseModel


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

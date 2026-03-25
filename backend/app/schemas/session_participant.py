from datetime import datetime

from pydantic import BaseModel

from app.schemas.ai_character import AiCharacterResponse


class SessionParticipantCreateRequest(BaseModel):
    session_id: int
    ai_character_id: int
    display_name: str
    role: str
    seat_index: int


class SessionParticipantBulkCreateRequest(BaseModel):
    participants: list[SessionParticipantCreateRequest]


class SessionParticipantResponse(BaseModel):
    id: int
    session_id: int
    ai_character_id: int
    display_name: str
    role: str
    seat_index: int
    is_active: bool
    created_at: datetime
    ai_character: AiCharacterResponse | None = None

    model_config = {"from_attributes": True}

from datetime import datetime

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}

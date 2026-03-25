from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class SessionMessageCreateRequest(BaseModel):
    session_id: int
    participant_id: int | None = None
    sequence_no: int
    content: str
    transcript_confidence: Decimal | None = None


class SessionMessageResponse(BaseModel):
    id: int
    session_id: int
    participant_id: int | None
    sequence_no: int
    content: str
    transcript_confidence: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class SessionFeedbackCreateRequest(BaseModel):
    session_id: int
    user_id: int
    summary_title: str
    positive_points: Any
    improvement_points: Any
    short_comment: str | None = None
    closing_message: str | None = None


class SessionFeedbackResponse(BaseModel):
    id: int
    session_id: int
    user_id: int
    summary_title: str
    short_comment: str | None
    positive_points: Any
    improvement_points: Any
    closing_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

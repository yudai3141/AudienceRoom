from datetime import datetime

from pydantic import BaseModel


class PracticeSessionCreateRequest(BaseModel):
    user_id: int
    mode: str
    participant_count: int
    feedback_enabled: bool = True
    theme: str | None = None
    presentation_duration_sec: int | None = None
    presentation_qa_count: int | None = None
    user_goal: str | None = None
    user_concerns: str | None = None
    session_brief: str | None = None
    target_context: str | None = None


class PracticeSessionStatusUpdateRequest(BaseModel):
    status: str


class PracticeSessionResponse(BaseModel):
    id: int
    user_id: int
    status: str
    mode: str
    participant_count: int
    feedback_enabled: bool
    theme: str | None
    presentation_duration_sec: int | None
    presentation_qa_count: int | None
    user_goal: str | None
    user_concerns: str | None
    session_brief: str | None
    target_context: str | None
    overall_score: int | None
    feedback_summary: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

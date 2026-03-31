from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.feedback_metric import FeedbackMetricResponse
from app.schemas.session_message import SessionMessageResponse
from app.schemas.session_participant import SessionParticipantResponse


class PracticeSessionCreateRequest(BaseModel):
    user_id: int
    mode: str
    participant_count: int = Field(..., ge=1, le=10)
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


class SessionFeedbackNested(BaseModel):
    id: int
    summary_title: str
    short_comment: str | None
    positive_points: Any
    improvement_points: Any
    closing_message: str | None
    created_at: datetime
    metrics: list[FeedbackMetricResponse] = []

    model_config = {"from_attributes": True}


class PracticeSessionDetailResponse(BaseModel):
    """Full session detail: session + participants + messages + feedback."""
    id: int
    user_id: int
    status: str
    mode: str
    participant_count: int
    feedback_enabled: bool
    theme: str | None
    overall_score: int | None
    feedback_summary: str | None
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime
    participants: list[SessionParticipantResponse] = []
    messages: list[SessionMessageResponse] = []
    feedback: SessionFeedbackNested | None = None


class SessionListItem(BaseModel):
    """Lightweight item for session history list."""
    id: int
    status: str
    mode: str
    theme: str | None
    overall_score: int | None
    has_feedback: bool
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime


class PaginatedSessionListResponse(BaseModel):
    items: list[SessionListItem]
    total: int
    limit: int
    offset: int


class DashboardResponse(BaseModel):
    total_sessions: int
    completed_sessions: int
    average_score: float | None
    recent_sessions: list[SessionListItem]


class FeedbackGenerationResponse(BaseModel):
    """Response for feedback generation API."""

    session_id: int
    feedback_id: int
    overall_score: int
    summary_title: str
    short_comment: str | None

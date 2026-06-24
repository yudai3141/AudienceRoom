from datetime import datetime

from pydantic import BaseModel, Field


class TopicCreateRequest(BaseModel):
    user_id: int
    title: str = Field(..., min_length=1, max_length=120)
    description: str | None = None


class TopicUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=120)
    description: str | None = None
    status: str | None = None


class TopicNodeResponse(BaseModel):
    id: int
    node_type: str | None
    label: str
    detail: str | None
    coverage: str
    sort_order: int

    model_config = {"from_attributes": True}


class TopicEdgeResponse(BaseModel):
    id: int
    source_node_id: int
    target_node_id: int
    relation_type: str

    model_config = {"from_attributes": True}


class TopicResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str | None
    status: str
    completeness_score: int | None
    current_summary: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TopicDetailResponse(TopicResponse):
    nodes: list[TopicNodeResponse]
    edges: list[TopicEdgeResponse]

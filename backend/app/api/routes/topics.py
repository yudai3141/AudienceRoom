from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.topic import (
    TopicCreateRequest,
    TopicDetailResponse,
    TopicEdgeResponse,
    TopicNodeResponse,
    TopicResponse,
    TopicUpdateRequest,
)
from app.services.topic_service import TopicService

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post("", response_model=TopicResponse, status_code=201)
def create_topic(
    body: TopicCreateRequest,
    db: Session = Depends(get_db),
) -> TopicResponse:
    service = TopicService(db)
    try:
        topic = service.create_topic(
            user_id=body.user_id,
            title=body.title,
            description=body.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return TopicResponse.model_validate(topic)


@router.get("", response_model=list[TopicResponse])
def list_topics(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
) -> list[TopicResponse]:
    service = TopicService(db)
    return [TopicResponse.model_validate(t) for t in service.list_user_topics(user_id)]


@router.get("/{topic_id}", response_model=TopicDetailResponse)
def get_topic_detail(
    topic_id: int,
    db: Session = Depends(get_db),
) -> TopicDetailResponse:
    service = TopicService(db)
    topic = service.get_topic(topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
    base = TopicResponse.model_validate(topic)
    return TopicDetailResponse(
        **base.model_dump(),
        nodes=[TopicNodeResponse.model_validate(n) for n in service.list_nodes(topic_id)],
        edges=[TopicEdgeResponse.model_validate(e) for e in service.list_edges(topic_id)],
    )


@router.patch("/{topic_id}", response_model=TopicResponse)
def update_topic(
    topic_id: int,
    body: TopicUpdateRequest,
    db: Session = Depends(get_db),
) -> TopicResponse:
    service = TopicService(db)
    try:
        topic = service.update_topic(
            topic_id,
            title=body.title,
            description=body.description,
            status=body.status,
        )
    except ValueError as e:
        # not found か invalid 値か。存在しないものは 404、それ以外は 400。
        status_code = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    return TopicResponse.model_validate(topic)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(
    topic_id: int,
    db: Session = Depends(get_db),
) -> None:
    service = TopicService(db)
    try:
        service.delete_topic(topic_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

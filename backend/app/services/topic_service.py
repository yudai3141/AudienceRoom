from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models.topic import TOPIC_STATUSES, Topic
from app.repositories.topic_repository import TopicRepository


class TopicService:
    """トピック (記憶層) の CRUD と概要更新を担う。LLM には依存しない。

    グラフ (nodes/edges) の更新は仮想 GraphRAG 側のサービスが担当する。
    """

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = TopicRepository(db)

    def create_topic(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
    ) -> Topic:
        title = (title or "").strip()
        if not title:
            raise ValueError("title must not be empty")

        topic = Topic(user_id=user_id, title=title, description=description)
        return self._repository.create(topic)

    def get_topic(self, topic_id: int) -> Topic | None:
        return self._repository.get_by_id(topic_id)

    def list_user_topics(self, user_id: int) -> list[Topic]:
        return self._repository.list_by_user_id(user_id)

    def update_topic(
        self,
        topic_id: int,
        *,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> Topic:
        topic = self._require_topic(topic_id)

        if title is not None:
            title = title.strip()
            if not title:
                raise ValueError("title must not be empty")
            topic.title = title
        if description is not None:
            topic.description = description
        if status is not None:
            if status not in TOPIC_STATUSES:
                raise ValueError(
                    f"Invalid status '{status}'. Must be one of {TOPIC_STATUSES}"
                )
            topic.status = status

        return self._repository.update(topic)

    def update_memory(
        self,
        topic_id: int,
        *,
        completeness_score: int | None = None,
        current_summary: str | None = None,
    ) -> Topic:
        """練習後に AI が生成したトピック概要を反映する。"""
        topic = self._require_topic(topic_id)

        if completeness_score is not None:
            if not 0 <= completeness_score <= 100:
                raise ValueError("completeness_score must be between 0 and 100")
            topic.completeness_score = completeness_score
        if current_summary is not None:
            topic.current_summary = current_summary

        return self._repository.update(topic)

    def delete_topic(self, topic_id: int) -> None:
        """論理削除 (deleted_at をセット)。"""
        topic = self._require_topic(topic_id)
        topic.deleted_at = datetime.now(timezone.utc)
        self._repository.update(topic)

    def _require_topic(self, topic_id: int) -> Topic:
        topic = self._repository.get_by_id(topic_id)
        if topic is None:
            raise ValueError(f"Topic with id {topic_id} not found")
        return topic

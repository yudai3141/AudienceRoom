from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.topic import Topic


class TopicRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, topic: Topic) -> Topic:
        self._db.add(topic)
        self._db.commit()
        self._db.refresh(topic)
        return topic

    def get_by_id(self, topic_id: int) -> Topic | None:
        stmt = select(Topic).where(
            Topic.id == topic_id,
            Topic.deleted_at.is_(None),
        )
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_user_id(self, user_id: int) -> list[Topic]:
        """ユーザの有効トピック一覧 (新しい順)。"""
        stmt = (
            select(Topic)
            .where(
                Topic.user_id == user_id,
                Topic.deleted_at.is_(None),
            )
            .order_by(Topic.updated_at.desc())
        )
        return list(self._db.execute(stmt).scalars().all())

    def update(self, topic: Topic) -> Topic:
        self._db.commit()
        self._db.refresh(topic)
        return topic

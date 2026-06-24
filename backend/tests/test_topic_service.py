"""TopicService のテスト (Plan B Phase B-1)。"""
import pytest
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.services.topic_service import TopicService


def _create_user(db: Session, suffix: str = "") -> User:
    user = User(
        firebase_uid=f"topic_svc_user{suffix}",
        email=f"topic_svc{suffix}@example.com",
        display_name="Topic Svc User",
    )
    db.add(user)
    db.flush()
    return user


class TestCreateTopic:
    def test_create(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        topic = svc.create_topic(user.id, "研究内容", description="PTSDモデル")

        assert topic.id is not None
        assert topic.title == "研究内容"
        assert topic.description == "PTSDモデル"
        assert topic.status == "active"

    def test_title_trimmed(self, db: Session) -> None:
        user = _create_user(db)
        topic = TopicService(db).create_topic(user.id, "  研究内容  ")
        assert topic.title == "研究内容"

    def test_empty_title_rejected(self, db: Session) -> None:
        user = _create_user(db)
        with pytest.raises(ValueError):
            TopicService(db).create_topic(user.id, "   ")


class TestReadTopics:
    def test_get_and_list(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        a = svc.create_topic(user.id, "A")
        svc.create_topic(user.id, "B")

        assert svc.get_topic(a.id).id == a.id
        assert svc.get_topic(999999) is None
        assert {t.title for t in svc.list_user_topics(user.id)} == {"A", "B"}


class TestUpdateTopic:
    def test_update_fields(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        topic = svc.create_topic(user.id, "x")
        updated = svc.update_topic(
            topic.id, title="研究内容", description="d", status="archived"
        )
        assert updated.title == "研究内容"
        assert updated.description == "d"
        assert updated.status == "archived"

    def test_invalid_status_rejected(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        topic = svc.create_topic(user.id, "x")
        with pytest.raises(ValueError):
            svc.update_topic(topic.id, status="bogus")

    def test_not_found_rejected(self, db: Session) -> None:
        with pytest.raises(ValueError):
            TopicService(db).update_topic(999999, title="x")


class TestUpdateMemory:
    def test_update_completeness_and_summary(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        topic = svc.create_topic(user.id, "x")
        updated = svc.update_memory(
            topic.id, completeness_score=65, current_summary="設計意図は説明できている"
        )
        assert updated.completeness_score == 65
        assert updated.current_summary == "設計意図は説明できている"

    def test_score_out_of_range_rejected(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        topic = svc.create_topic(user.id, "x")
        with pytest.raises(ValueError):
            svc.update_memory(topic.id, completeness_score=120)


class TestDeleteTopic:
    def test_soft_delete(self, db: Session) -> None:
        user = _create_user(db)
        svc = TopicService(db)
        topic = svc.create_topic(user.id, "x")
        svc.delete_topic(topic.id)
        assert svc.get_topic(topic.id) is None

    def test_delete_not_found(self, db: Session) -> None:
        with pytest.raises(ValueError):
            TopicService(db).delete_topic(999999)

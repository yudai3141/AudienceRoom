"""topics / topic_nodes / topic_edges モデルと制約のテスト (Plan B Phase B-1)。

リポジトリ層はまだ無いため、モデルと DB 制約 (CHECK / UNIQUE / FK link) を直接検証する。
"""
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.topic import Topic
from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode
from app.db.models.user import User


def _create_user(db: Session, suffix: str = "") -> User:
    user = User(
        firebase_uid=f"topic_user{suffix}",
        email=f"topic{suffix}@example.com",
        display_name="Topic User",
    )
    db.add(user)
    db.flush()
    return user


def _create_topic(db: Session, user: User) -> Topic:
    topic = Topic(user_id=user.id, title="研究内容")
    db.add(topic)
    db.flush()
    return topic


class TestTopicModel:
    def test_create_topic_defaults(self, db: Session) -> None:
        user = _create_user(db)
        topic = _create_topic(db, user)

        assert topic.id is not None
        assert topic.user_id == user.id
        assert topic.title == "研究内容"
        assert topic.status == "active"
        assert topic.completeness_score is None
        assert topic.current_summary is None
        assert topic.deleted_at is None

    def test_invalid_status_rejected(self, db: Session) -> None:
        user = _create_user(db)
        db.add(Topic(user_id=user.id, title="x", status="bogus"))
        with pytest.raises(IntegrityError):
            db.flush()

    def test_completeness_score_out_of_range_rejected(self, db: Session) -> None:
        user = _create_user(db)
        db.add(Topic(user_id=user.id, title="x", completeness_score=120))
        with pytest.raises(IntegrityError):
            db.flush()


class TestTopicNode:
    def test_node_defaults_and_relationship(self, db: Session) -> None:
        user = _create_user(db)
        topic = _create_topic(db, user)
        node = TopicNode(topic_id=topic.id, label="PTSD患者モデル", node_type="theme")
        db.add(node)
        db.flush()

        assert node.coverage == "gap"
        assert node.sort_order == 0
        db.refresh(topic)
        assert node in topic.nodes

    def test_invalid_coverage_rejected(self, db: Session) -> None:
        user = _create_user(db)
        topic = _create_topic(db, user)
        db.add(TopicNode(topic_id=topic.id, label="x", coverage="unknown"))
        with pytest.raises(IntegrityError):
            db.flush()


class TestTopicEdge:
    def test_contradicts_edge(self, db: Session) -> None:
        user = _create_user(db)
        topic = _create_topic(db, user)
        a = TopicNode(topic_id=topic.id, label="主導した")
        b = TopicNode(topic_id=topic.id, label="チームで決めた")
        db.add_all([a, b])
        db.flush()

        edge = TopicEdge(
            topic_id=topic.id,
            source_node_id=a.id,
            target_node_id=b.id,
            relation_type="contradicts",
        )
        db.add(edge)
        db.flush()

        db.refresh(topic)
        assert edge in topic.edges
        assert edge.relation_type == "contradicts"

    def test_duplicate_edge_rejected(self, db: Session) -> None:
        user = _create_user(db)
        topic = _create_topic(db, user)
        a = TopicNode(topic_id=topic.id, label="手法")
        b = TopicNode(topic_id=topic.id, label="成果")
        db.add_all([a, b])
        db.flush()

        db.add(TopicEdge(topic_id=topic.id, source_node_id=a.id, target_node_id=b.id, relation_type="leads_to"))
        db.flush()
        db.add(TopicEdge(topic_id=topic.id, source_node_id=a.id, target_node_id=b.id, relation_type="leads_to"))
        with pytest.raises(IntegrityError):
            db.flush()


class TestPracticeSessionTopicLink:
    def test_session_links_topic(self, db: Session) -> None:
        user = _create_user(db)
        topic = _create_topic(db, user)
        session = PracticeSession(
            user_id=user.id,
            topic_id=topic.id,
            mode="interview",
            participant_count=2,
        )
        db.add(session)
        db.flush()

        assert session.topic_id == topic.id
        assert session.topic.id == topic.id

    def test_topic_id_is_optional(self, db: Session) -> None:
        user = _create_user(db)
        session = PracticeSession(user_id=user.id, mode="free_conversation", participant_count=1)
        db.add(session)
        db.flush()

        assert session.topic_id is None

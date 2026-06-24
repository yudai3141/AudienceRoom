"""会話ターンへのトピック記憶注入 (仮想 GraphRAG) の統合テスト。"""
from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.topic import Topic
from app.db.models.topic_node import TopicNode
from app.db.models.user import User
from app.repositories.topic_node_repository import TopicNodeRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.streaming_conversation_service import StreamingConversationService
from app.services.ai.topic_context_loader import load_topic_memory_context
from app.services.practice_session_service import PracticeSessionService


def _user(db: Session, suffix: str = "") -> User:
    u = User(
        firebase_uid=f"conv_topic_user{suffix}",
        email=f"conv_topic{suffix}@example.com",
        display_name="Conv Topic User",
    )
    db.add(u)
    db.flush()
    return u


def _topic_with_node(db: Session, user: User) -> Topic:
    topic = TopicRepository(db).create(Topic(user_id=user.id, title="研究内容"))
    TopicNodeRepository(db).create(
        TopicNode(topic_id=topic.id, label="評価方法", coverage="weak")
    )
    return topic


class TestSessionTopicLink:
    def test_create_session_with_topic_id(self, db: Session) -> None:
        user = _user(db)
        topic = _topic_with_node(db, user)
        session = PracticeSessionService(db).create_session(
            user_id=user.id,
            mode="interview",
            participant_count=1,
            topic_id=topic.id,
        )
        assert session.topic_id == topic.id

    def test_topic_id_optional(self, db: Session) -> None:
        user = _user(db)
        session = PracticeSessionService(db).create_session(
            user_id=user.id, mode="free_conversation", participant_count=1
        )
        assert session.topic_id is None


class TestLoadTopicMemoryContext:
    def test_none_topic_returns_none(self, db: Session) -> None:
        assert load_topic_memory_context(db, None) is None

    def test_loads_graph_context(self, db: Session) -> None:
        user = _user(db)
        topic = _topic_with_node(db, user)
        text = load_topic_memory_context(db, topic.id)
        assert text is not None
        assert "評価方法" in text


class TestStreamingPromptInjection:
    def test_prompt_includes_topic_memory(self, db: Session) -> None:
        user = _user(db)
        topic = _topic_with_node(db, user)
        session = PracticeSession(
            user_id=user.id, topic_id=topic.id, mode="interview", participant_count=1
        )
        service = StreamingConversationService(db)
        messages = service._build_prompt(session, [], None)
        assert "過去に話した内容" in messages[0].content
        assert "評価方法" in messages[0].content

    def test_prompt_without_topic_has_no_memory(self, db: Session) -> None:
        user = _user(db)
        session = PracticeSession(
            user_id=user.id, topic_id=None, mode="interview", participant_count=1
        )
        service = StreamingConversationService(db)
        messages = service._build_prompt(session, [], None)
        assert "過去に話した内容" not in messages[0].content

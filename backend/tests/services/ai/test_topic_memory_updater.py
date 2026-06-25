"""TopicMemoryUpdater（練習後のトピック更新, Plan B B-2）のテスト。LLM はモック。"""
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.orm import Session

from app.db.models.practice_session import PracticeSession
from app.db.models.session_message import SessionMessage
from app.db.models.topic import Topic
from app.db.models.topic_node import TopicNode
from app.db.models.user import User
from app.repositories.topic_node_repository import TopicNodeRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.topic_memory_updater import (
    TopicMemoryUpdater,
    compute_completeness,
)


def _user(db: Session, s: str = "") -> User:
    u = User(firebase_uid=f"tmu{s}", email=f"tmu{s}@e.com", display_name="TMU")
    db.add(u)
    db.flush()
    return u


def _updater(db: Session, json_return: dict):
    llm = MagicMock()
    llm.generate_json = AsyncMock(return_value=json_return)
    return TopicMemoryUpdater(db, llm=llm)


def _session(db: Session, user: User, topic_id: int | None) -> PracticeSession:
    s = PracticeSession(
        user_id=user.id, topic_id=topic_id, mode="interview",
        participant_count=1, status="completed",
    )
    db.add(s)
    db.flush()
    db.add(SessionMessage(session_id=s.id, participant_id=None, sequence_no=1, content="評価は15%改善しました"))
    db.flush()
    return s


class TestComputeCompleteness:
    def test_none_for_empty(self) -> None:
        assert compute_completeness([]) is None

    def test_ratio(self) -> None:
        nodes = [
            TopicNode(topic_id=1, label="a", coverage="covered"),
            TopicNode(topic_id=1, label="b", coverage="covered"),
            TopicNode(topic_id=1, label="c", coverage="weak"),
            TopicNode(topic_id=1, label="d", coverage="gap"),
        ]
        assert compute_completeness(nodes) == 50


class TestUpdateFromSession:
    async def test_skipped_without_topic(self, db: Session) -> None:
        user = _user(db)
        session = _session(db, user, topic_id=None)
        result = await _updater(db, {}).update_from_session(session.id)
        assert result.skipped is True

    async def test_updates_graph_completeness_and_summary(self, db: Session) -> None:
        user = _user(db, "2")
        topic = TopicRepository(db).create(
            Topic(user_id=user.id, title="研究内容", completeness_score=0)
        )
        node_repo = TopicNodeRepository(db)
        node_repo.create(TopicNode(topic_id=topic.id, label="評価方法", coverage="weak"))
        node_repo.create(TopicNode(topic_id=topic.id, label="研究テーマ", coverage="covered"))
        session = _session(db, user, topic_id=topic.id)

        updater = _updater(
            db,
            {
                "nodes": [{"label": "評価方法", "coverage": "covered", "detail": "15%改善"}],
                "edges": [],
                "current_summary": "評価方法も説明できるようになった",
            },
        )
        result = await updater.update_from_session(session.id)

        assert result.skipped is False
        # 評価方法 weak -> covered に更新（2/2 covered = 100）
        assert result.completeness_after == 100
        assert result.current_summary == "評価方法も説明できるようになった"
        assert any(c["label"] == "評価方法" and c["after"] == "covered" for c in result.coverage_changes)

        refreshed = TopicRepository(db).get_by_id(topic.id)
        assert refreshed.completeness_score == 100
        assert refreshed.current_summary == "評価方法も説明できるようになった"

    async def test_session_not_found(self, db: Session) -> None:
        import pytest

        with pytest.raises(ValueError):
            await _updater(db, {}).update_from_session(999999)

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.models.practice_session import PracticeSession
from app.db.models.session_message import SessionMessage
from app.db.models.topic import Topic
from app.db.models.topic_node import TopicNode
from app.db.models.user import User
from app.db.session import get_db
from app.main import app as fastapi_app
import app.db.models  # noqa: F401

engine = create_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture()
def db_session() -> Session:
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    def _override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


def _mock_llm(json_return: dict):
    m = MagicMock()
    m.generate_json = AsyncMock(return_value=json_return)
    return m


def _user(db: Session, s: str) -> User:
    u = User(firebase_uid=f"upd_api{s}", email=f"upd_api{s}@e.com", display_name="U")
    db.add(u)
    db.flush()
    return u


def _session(db: Session, user_id: int, topic_id: int | None) -> PracticeSession:
    s = PracticeSession(
        user_id=user_id, topic_id=topic_id, mode="interview",
        participant_count=1, status="completed",
    )
    db.add(s)
    db.flush()
    db.add(SessionMessage(session_id=s.id, participant_id=None, sequence_no=1, content="15%改善しました"))
    db.flush()
    return s


class TestUpdateTopicAPI:
    def test_update_applies_and_returns_diff(self, client: TestClient, db_session: Session) -> None:
        user = _user(db_session, "1")
        topic = Topic(user_id=user.id, title="研究内容", completeness_score=0)
        db_session.add(topic)
        db_session.flush()
        db_session.add(TopicNode(topic_id=topic.id, label="評価方法", coverage="weak"))
        db_session.flush()
        session = _session(db_session, user.id, topic.id)

        mock = _mock_llm(
            {"nodes": [{"label": "評価方法", "coverage": "covered"}], "edges": [], "current_summary": "s"}
        )
        with patch("app.services.ai.topic_memory_updater.get_llm_provider", return_value=mock):
            res = client.post(f"/practice-sessions/{session.id}/update-topic")

        assert res.status_code == 200
        body = res.json()
        assert body["skipped"] is False
        assert body["topic_id"] == topic.id
        assert body["completeness_after"] == 100
        assert body["current_summary"] == "s"
        assert any(c["label"] == "評価方法" and c["after"] == "covered" for c in body["coverage_changes"])

    def test_skipped_without_topic(self, client: TestClient, db_session: Session) -> None:
        user = _user(db_session, "2")
        session = _session(db_session, user.id, None)
        mock = _mock_llm({})
        with patch("app.services.ai.topic_memory_updater.get_llm_provider", return_value=mock):
            res = client.post(f"/practice-sessions/{session.id}/update-topic")
        assert res.status_code == 200
        assert res.json()["skipped"] is True

    def test_session_not_found(self, client: TestClient) -> None:
        mock = _mock_llm({})
        with patch("app.services.ai.topic_memory_updater.get_llm_provider", return_value=mock):
            res = client.post("/practice-sessions/999999/update-topic")
        assert res.status_code == 400

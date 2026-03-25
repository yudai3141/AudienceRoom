import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
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
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(fastapi_app)
    fastapi_app.dependency_overrides.clear()


def _create_user(client: TestClient) -> int:
    resp = client.post("/users", json={
        "firebase_uid": "enhance_user", "email": "enhance@example.com",
        "display_name": "Enhance User",
    })
    return resp.json()["id"]


def _create_session(client: TestClient, user_id: int, mode: str = "interview") -> int:
    resp = client.post("/practice-sessions", json={
        "user_id": user_id, "mode": mode, "participant_count": 3,
    })
    return resp.json()["id"]


def _create_character(client: TestClient, code: str) -> int:
    resp = client.post("/ai-characters", json={
        "code": code, "name": f"Char {code}", "role": "interviewer",
        "strictness": "normal",
    })
    return resp.json()["id"]


class TestSessionDetailEndpoint:
    def test_detail_empty_session(self, client: TestClient) -> None:
        user_id = _create_user(client)
        session_id = _create_session(client, user_id)

        response = client.get(f"/practice-sessions/{session_id}/detail")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["participants"] == []
        assert data["messages"] == []
        assert data["feedback"] is None

    def test_detail_with_participants(self, client: TestClient) -> None:
        user_id = _create_user(client)
        session_id = _create_session(client, user_id)
        char_id = _create_character(client, "detail_char")

        client.post("/session-participants", json={
            "session_id": session_id, "ai_character_id": char_id,
            "display_name": "Test Char", "role": "audience", "seat_index": 0,
        })

        response = client.get(f"/practice-sessions/{session_id}/detail")
        data = response.json()
        assert len(data["participants"]) == 1
        p = data["participants"][0]
        assert p["ai_character"]["code"] == "detail_char"
        assert p["ai_character"]["name"] == "Char detail_char"

    def test_detail_with_messages(self, client: TestClient) -> None:
        user_id = _create_user(client)
        session_id = _create_session(client, user_id)
        client.post("/session-messages", json={
            "session_id": session_id, "sequence_no": 1, "content": "Hello",
        })

        response = client.get(f"/practice-sessions/{session_id}/detail")
        data = response.json()
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Hello"

    def test_detail_with_feedback_and_metrics(self, client: TestClient) -> None:
        user_id = _create_user(client)
        session_id = _create_session(client, user_id)

        fb_resp = client.post("/session-feedback", json={
            "session_id": session_id, "user_id": user_id,
            "summary_title": "Good", "positive_points": ["A"],
            "improvement_points": ["B"],
        })
        feedback_id = fb_resp.json()["id"]
        client.post("/feedback-metrics", json={
            "feedback_id": feedback_id, "metric_key": "clarity",
            "metric_value": "85.00",
        })

        response = client.get(f"/practice-sessions/{session_id}/detail")
        data = response.json()
        assert data["feedback"]["summary_title"] == "Good"
        assert len(data["feedback"]["metrics"]) == 1
        assert data["feedback"]["metrics"][0]["metric_key"] == "clarity"

    def test_detail_not_found(self, client: TestClient) -> None:
        response = client.get("/practice-sessions/99999/detail")
        assert response.status_code == 404


class TestPaginatedSessionList:
    def test_pagination(self, client: TestClient) -> None:
        user_id = _create_user(client)
        for _ in range(5):
            _create_session(client, user_id)

        resp = client.get(f"/practice-sessions?user_id={user_id}&limit=2&offset=0")
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    def test_pagination_offset(self, client: TestClient) -> None:
        user_id = _create_user(client)
        for _ in range(5):
            _create_session(client, user_id)

        resp = client.get(f"/practice-sessions?user_id={user_id}&limit=3&offset=3")
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2

    def test_has_feedback_flag(self, client: TestClient) -> None:
        user_id = _create_user(client)
        s1 = _create_session(client, user_id)
        s2 = _create_session(client, user_id, mode="presentation")

        client.post("/session-feedback", json={
            "session_id": s1, "user_id": user_id,
            "summary_title": "FB", "positive_points": [],
            "improvement_points": [],
        })

        resp = client.get(f"/practice-sessions?user_id={user_id}")
        items = {i["id"]: i for i in resp.json()["items"]}
        assert items[s1]["has_feedback"] is True
        assert items[s2]["has_feedback"] is False


class TestParticipantAiCharacterNested:
    def test_participant_includes_character(self, client: TestClient) -> None:
        user_id = _create_user(client)
        session_id = _create_session(client, user_id)
        char_id = _create_character(client, "nested_char")

        client.post("/session-participants", json={
            "session_id": session_id, "ai_character_id": char_id,
            "display_name": "Nested", "role": "audience", "seat_index": 0,
        })

        resp = client.get(f"/practice-sessions/{session_id}/detail")
        p = resp.json()["participants"][0]
        assert p["ai_character"] is not None
        assert p["ai_character"]["personality"] is None

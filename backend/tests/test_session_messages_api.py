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


def _create_session(client: TestClient) -> int:
    user_resp = client.post("/users", json={
        "firebase_uid": "sm_api_user", "email": "sm_api@example.com",
        "display_name": "SM API User",
    })
    user_id = user_resp.json()["id"]
    session_resp = client.post("/practice-sessions", json={
        "user_id": user_id, "mode": "interview", "participant_count": 2,
    })
    return session_resp.json()["id"]


class TestSessionMessagesAPI:
    def test_create_message(self, client: TestClient) -> None:
        session_id = _create_session(client)
        response = client.post("/session-messages", json={
            "session_id": session_id, "sequence_no": 1,
            "content": "よろしくお願いします",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == session_id
        assert data["content"] == "よろしくお願いします"
        assert data["sequence_no"] == 1

    def test_create_message_with_confidence(self, client: TestClient) -> None:
        session_id = _create_session(client)
        response = client.post("/session-messages", json={
            "session_id": session_id, "sequence_no": 1,
            "content": "信頼度テスト", "transcript_confidence": "0.920",
        })
        assert response.status_code == 201
        assert response.json()["transcript_confidence"] == "0.920"

    def test_list_messages(self, client: TestClient) -> None:
        session_id = _create_session(client)
        client.post("/session-messages", json={
            "session_id": session_id, "sequence_no": 1, "content": "1つ目",
        })
        client.post("/session-messages", json={
            "session_id": session_id, "sequence_no": 2, "content": "2つ目",
        })

        response = client.get(f"/session-messages?session_id={session_id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["sequence_no"] == 1

    def test_get_message(self, client: TestClient) -> None:
        session_id = _create_session(client)
        create_resp = client.post("/session-messages", json={
            "session_id": session_id, "sequence_no": 1, "content": "取得テスト",
        })
        message_id = create_resp.json()["id"]

        response = client.get(f"/session-messages/{message_id}")
        assert response.status_code == 200
        assert response.json()["content"] == "取得テスト"

    def test_get_message_not_found(self, client: TestClient) -> None:
        response = client.get("/session-messages/99999")
        assert response.status_code == 404

    def test_create_message_missing_fields(self, client: TestClient) -> None:
        response = client.post("/session-messages", json={"session_id": 1})
        assert response.status_code == 422

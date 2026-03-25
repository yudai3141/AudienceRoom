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
    response = client.post(
        "/users",
        json={
            "firebase_uid": "ps_api_user",
            "email": "ps_api@example.com",
            "display_name": "PS API User",
        },
    )
    return response.json()["id"]


class TestPracticeSessionsAPI:
    def test_create_session(self, client: TestClient) -> None:
        user_id = _create_user(client)
        response = client.post(
            "/practice-sessions",
            json={
                "user_id": user_id,
                "mode": "interview",
                "participant_count": 3,
                "theme": "エンジニア面接",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == user_id
        assert data["status"] == "waiting"
        assert data["mode"] == "interview"
        assert data["participant_count"] == 3
        assert data["theme"] == "エンジニア面接"

    def test_create_session_invalid_mode(self, client: TestClient) -> None:
        user_id = _create_user(client)
        response = client.post(
            "/practice-sessions",
            json={
                "user_id": user_id,
                "mode": "invalid",
                "participant_count": 1,
            },
        )
        assert response.status_code == 400

    def test_create_session_with_optional_fields(self, client: TestClient) -> None:
        user_id = _create_user(client)
        response = client.post(
            "/practice-sessions",
            json={
                "user_id": user_id,
                "mode": "presentation",
                "participant_count": 5,
                "feedback_enabled": True,
                "presentation_duration_sec": 300,
                "presentation_qa_count": 3,
                "user_goal": "堂々と話す",
                "user_concerns": "緊張しやすい",
                "target_context": "presentation",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["presentation_duration_sec"] == 300
        assert data["presentation_qa_count"] == 3

    def test_get_session(self, client: TestClient) -> None:
        user_id = _create_user(client)
        create_resp = client.post(
            "/practice-sessions",
            json={
                "user_id": user_id,
                "mode": "interview",
                "participant_count": 2,
            },
        )
        session_id = create_resp.json()["id"]

        response = client.get(f"/practice-sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["id"] == session_id

    def test_get_session_not_found(self, client: TestClient) -> None:
        response = client.get("/practice-sessions/99999")
        assert response.status_code == 404

    def test_list_sessions(self, client: TestClient) -> None:
        user_id = _create_user(client)
        client.post(
            "/practice-sessions",
            json={"user_id": user_id, "mode": "interview", "participant_count": 2},
        )
        client.post(
            "/practice-sessions",
            json={"user_id": user_id, "mode": "presentation", "participant_count": 4},
        )

        response = client.get(f"/practice-sessions?user_id={user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_update_status_to_active(self, client: TestClient) -> None:
        user_id = _create_user(client)
        create_resp = client.post(
            "/practice-sessions",
            json={"user_id": user_id, "mode": "interview", "participant_count": 3},
        )
        session_id = create_resp.json()["id"]

        response = client.patch(
            f"/practice-sessions/{session_id}/status",
            json={"status": "active"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "active"
        assert response.json()["started_at"] is not None

    def test_update_status_to_completed(self, client: TestClient) -> None:
        user_id = _create_user(client)
        create_resp = client.post(
            "/practice-sessions",
            json={"user_id": user_id, "mode": "interview", "participant_count": 3},
        )
        session_id = create_resp.json()["id"]

        client.patch(
            f"/practice-sessions/{session_id}/status",
            json={"status": "active"},
        )
        response = client.patch(
            f"/practice-sessions/{session_id}/status",
            json={"status": "completed"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "completed"
        assert response.json()["ended_at"] is not None

    def test_update_status_invalid_transition(self, client: TestClient) -> None:
        user_id = _create_user(client)
        create_resp = client.post(
            "/practice-sessions",
            json={"user_id": user_id, "mode": "interview", "participant_count": 3},
        )
        session_id = create_resp.json()["id"]

        response = client.patch(
            f"/practice-sessions/{session_id}/status",
            json={"status": "completed"},
        )
        assert response.status_code == 400

    def test_create_session_missing_fields(self, client: TestClient) -> None:
        response = client.post(
            "/practice-sessions",
            json={"mode": "interview"},
        )
        assert response.status_code == 422

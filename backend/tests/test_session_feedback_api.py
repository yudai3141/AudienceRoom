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


def _create_prerequisites(client: TestClient) -> tuple[int, int]:
    user_resp = client.post("/users", json={
        "firebase_uid": "sf_api_user", "email": "sf_api@example.com",
        "display_name": "SF API User",
    })
    user_id = user_resp.json()["id"]
    session_resp = client.post("/practice-sessions", json={
        "user_id": user_id, "mode": "interview", "participant_count": 3,
    })
    return session_resp.json()["id"], user_id


class TestSessionFeedbackAPI:
    def test_create_feedback(self, client: TestClient) -> None:
        session_id, user_id = _create_prerequisites(client)
        response = client.post("/session-feedback", json={
            "session_id": session_id, "user_id": user_id,
            "summary_title": "よくできました",
            "positive_points": ["声が大きい", "論理的"],
            "improvement_points": ["結論を先に"],
            "short_comment": "お疲れ様",
            "closing_message": "次回も頑張りましょう",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["summary_title"] == "よくできました"
        assert data["positive_points"] == ["声が大きい", "論理的"]

    def test_create_feedback_duplicate(self, client: TestClient) -> None:
        session_id, user_id = _create_prerequisites(client)
        client.post("/session-feedback", json={
            "session_id": session_id, "user_id": user_id,
            "summary_title": "1回目",
            "positive_points": [], "improvement_points": [],
        })
        response = client.post("/session-feedback", json={
            "session_id": session_id, "user_id": user_id,
            "summary_title": "2回目",
            "positive_points": [], "improvement_points": [],
        })
        assert response.status_code == 409

    def test_get_feedback_by_id(self, client: TestClient) -> None:
        session_id, user_id = _create_prerequisites(client)
        create_resp = client.post("/session-feedback", json={
            "session_id": session_id, "user_id": user_id,
            "summary_title": "ID取得テスト",
            "positive_points": [], "improvement_points": [],
        })
        feedback_id = create_resp.json()["id"]

        response = client.get(f"/session-feedback/{feedback_id}")
        assert response.status_code == 200
        assert response.json()["summary_title"] == "ID取得テスト"

    def test_get_feedback_by_id_not_found(self, client: TestClient) -> None:
        response = client.get("/session-feedback/99999")
        assert response.status_code == 404

    def test_get_feedback_by_session(self, client: TestClient) -> None:
        session_id, user_id = _create_prerequisites(client)
        client.post("/session-feedback", json={
            "session_id": session_id, "user_id": user_id,
            "summary_title": "セッション別取得",
            "positive_points": ["良い"], "improvement_points": ["改善"],
        })

        response = client.get(f"/session-feedback?session_id={session_id}")
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id

    def test_get_feedback_by_session_not_found(self, client: TestClient) -> None:
        response = client.get("/session-feedback?session_id=99999")
        assert response.status_code == 404

    def test_create_feedback_missing_fields(self, client: TestClient) -> None:
        response = client.post("/session-feedback", json={"session_id": 1})
        assert response.status_code == 422

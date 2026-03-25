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


def _create_feedback(client: TestClient) -> int:
    user_resp = client.post("/users", json={
        "firebase_uid": "fm_api_user", "email": "fm_api@example.com",
        "display_name": "FM API User",
    })
    user_id = user_resp.json()["id"]
    session_resp = client.post("/practice-sessions", json={
        "user_id": user_id, "mode": "interview", "participant_count": 3,
    })
    session_id = session_resp.json()["id"]
    feedback_resp = client.post("/session-feedback", json={
        "session_id": session_id, "user_id": user_id,
        "summary_title": "テスト",
        "positive_points": ["良い"], "improvement_points": ["改善"],
    })
    return feedback_resp.json()["id"]


class TestFeedbackMetricsAPI:
    def test_create_metric(self, client: TestClient) -> None:
        feedback_id = _create_feedback(client)
        response = client.post("/feedback-metrics", json={
            "feedback_id": feedback_id, "metric_key": "clarity",
            "metric_value": "85.50", "metric_label": "明瞭さ", "metric_unit": "点",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["metric_key"] == "clarity"
        assert data["metric_value"] == "85.50"

    def test_bulk_create_metrics(self, client: TestClient) -> None:
        feedback_id = _create_feedback(client)
        response = client.post("/feedback-metrics/bulk", json={
            "metrics": [
                {"feedback_id": feedback_id, "metric_key": "speed", "metric_value": "70.00"},
                {"feedback_id": feedback_id, "metric_key": "volume", "metric_value": "90.00", "metric_label": "声量", "metric_unit": "点"},
            ]
        })
        assert response.status_code == 201
        assert len(response.json()) == 2

    def test_list_metrics(self, client: TestClient) -> None:
        feedback_id = _create_feedback(client)
        client.post("/feedback-metrics", json={
            "feedback_id": feedback_id, "metric_key": "a", "metric_value": "1.00",
        })
        client.post("/feedback-metrics", json={
            "feedback_id": feedback_id, "metric_key": "b", "metric_value": "2.00",
        })

        response = client.get(f"/feedback-metrics?feedback_id={feedback_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_metric(self, client: TestClient) -> None:
        feedback_id = _create_feedback(client)
        create_resp = client.post("/feedback-metrics", json={
            "feedback_id": feedback_id, "metric_key": "test", "metric_value": "50.00",
        })
        metric_id = create_resp.json()["id"]

        response = client.get(f"/feedback-metrics/{metric_id}")
        assert response.status_code == 200
        assert response.json()["metric_key"] == "test"

    def test_get_metric_not_found(self, client: TestClient) -> None:
        response = client.get("/feedback-metrics/99999")
        assert response.status_code == 404

    def test_create_metric_missing_fields(self, client: TestClient) -> None:
        response = client.post("/feedback-metrics", json={"feedback_id": 1})
        assert response.status_code == 422

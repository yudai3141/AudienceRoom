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
    """Create user, session, character via API. Return (session_id, character_id)."""
    user_resp = client.post(
        "/users",
        json={
            "firebase_uid": "sp_api_user",
            "email": "sp_api@example.com",
            "display_name": "SP API User",
        },
    )
    user_id = user_resp.json()["id"]

    session_resp = client.post(
        "/practice-sessions",
        json={"user_id": user_id, "mode": "interview", "participant_count": 3},
    )
    session_id = session_resp.json()["id"]

    char_resp = client.post(
        "/ai-characters",
        json={
            "code": "sp_api_char",
            "name": "API面接官",
            "role": "host",
            "strictness": "normal",
        },
    )
    character_id = char_resp.json()["id"]

    return session_id, character_id


class TestSessionParticipantsAPI:
    def test_create_participant(self, client: TestClient) -> None:
        session_id, character_id = _create_prerequisites(client)

        response = client.post(
            "/session-participants",
            json={
                "session_id": session_id,
                "ai_character_id": character_id,
                "display_name": "API参加者",
                "role": "host",
                "seat_index": 0,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["session_id"] == session_id
        assert data["ai_character_id"] == character_id
        assert data["role"] == "host"
        assert data["is_active"] is True

    def test_create_participant_invalid_role(self, client: TestClient) -> None:
        session_id, character_id = _create_prerequisites(client)

        response = client.post(
            "/session-participants",
            json={
                "session_id": session_id,
                "ai_character_id": character_id,
                "display_name": "不正ロール",
                "role": "invalid",
                "seat_index": 0,
            },
        )
        assert response.status_code == 400

    def test_bulk_create_participants(self, client: TestClient) -> None:
        session_id, character_id = _create_prerequisites(client)

        response = client.post(
            "/session-participants/bulk",
            json={
                "participants": [
                    {
                        "session_id": session_id,
                        "ai_character_id": character_id,
                        "display_name": f"一括参加者{i}",
                        "role": "audience",
                        "seat_index": i,
                    }
                    for i in range(3)
                ]
            },
        )
        assert response.status_code == 201
        assert len(response.json()) == 3

    def test_list_participants(self, client: TestClient) -> None:
        session_id, character_id = _create_prerequisites(client)

        for i in range(2):
            client.post(
                "/session-participants",
                json={
                    "session_id": session_id,
                    "ai_character_id": character_id,
                    "display_name": f"一覧テスト{i}",
                    "role": "audience",
                    "seat_index": i,
                },
            )

        response = client.get(f"/session-participants?session_id={session_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_participant(self, client: TestClient) -> None:
        session_id, character_id = _create_prerequisites(client)

        create_resp = client.post(
            "/session-participants",
            json={
                "session_id": session_id,
                "ai_character_id": character_id,
                "display_name": "取得テスト",
                "role": "host",
                "seat_index": 0,
            },
        )
        participant_id = create_resp.json()["id"]

        response = client.get(f"/session-participants/{participant_id}")
        assert response.status_code == 200
        assert response.json()["display_name"] == "取得テスト"

    def test_get_participant_not_found(self, client: TestClient) -> None:
        response = client.get("/session-participants/99999")
        assert response.status_code == 404

    def test_create_participant_missing_fields(self, client: TestClient) -> None:
        response = client.post(
            "/session-participants",
            json={"session_id": 1},
        )
        assert response.status_code == 422

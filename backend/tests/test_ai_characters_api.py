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


class TestAiCharactersAPI:
    def test_create_ai_character(self, client: TestClient) -> None:
        response = client.post(
            "/ai-characters",
            json={
                "code": "api_host_01",
                "name": "API面接官",
                "role": "host",
                "strictness": "normal",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "api_host_01"
        assert data["name"] == "API面接官"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_ai_character_with_optional_fields(self, client: TestClient) -> None:
        response = client.post(
            "/ai-characters",
            json={
                "code": "api_host_02",
                "name": "詳細面接官",
                "role": "host",
                "strictness": "hard",
                "personality": "strict",
                "voice_style": "formal",
                "description": "厳しめの面接官キャラクター",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["personality"] == "strict"
        assert data["voice_style"] == "formal"
        assert data["description"] == "厳しめの面接官キャラクター"

    def test_create_ai_character_duplicate_code(self, client: TestClient) -> None:
        client.post(
            "/ai-characters",
            json={
                "code": "api_dup",
                "name": "First",
                "role": "host",
                "strictness": "gentle",
            },
        )
        response = client.post(
            "/ai-characters",
            json={
                "code": "api_dup",
                "name": "Second",
                "role": "audience",
                "strictness": "hard",
            },
        )
        assert response.status_code == 409

    def test_list_ai_characters(self, client: TestClient) -> None:
        client.post(
            "/ai-characters",
            json={
                "code": "api_list_01",
                "name": "List Test 1",
                "role": "host",
                "strictness": "gentle",
            },
        )
        client.post(
            "/ai-characters",
            json={
                "code": "api_list_02",
                "name": "List Test 2",
                "role": "audience",
                "strictness": "normal",
            },
        )

        response = client.get("/ai-characters")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_get_ai_character(self, client: TestClient) -> None:
        create_response = client.post(
            "/ai-characters",
            json={
                "code": "api_get_01",
                "name": "Get Test",
                "role": "host",
                "strictness": "normal",
            },
        )
        character_id = create_response.json()["id"]

        response = client.get(f"/ai-characters/{character_id}")
        assert response.status_code == 200
        assert response.json()["code"] == "api_get_01"

    def test_get_ai_character_not_found(self, client: TestClient) -> None:
        response = client.get("/ai-characters/99999")
        assert response.status_code == 404

    def test_create_ai_character_missing_fields(self, client: TestClient) -> None:
        response = client.post(
            "/ai-characters",
            json={"code": "incomplete"},
        )
        assert response.status_code == 422

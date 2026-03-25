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


class TestUsersAPI:
    def test_create_user(self, client: TestClient) -> None:
        response = client.post(
            "/users",
            json={
                "firebase_uid": "api_uid_001",
                "email": "api@example.com",
                "display_name": "API User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["firebase_uid"] == "api_uid_001"
        assert data["email"] == "api@example.com"
        assert data["display_name"] == "API User"
        assert "id" in data

    def test_create_user_with_photo_url(self, client: TestClient) -> None:
        response = client.post(
            "/users",
            json={
                "firebase_uid": "api_uid_photo",
                "email": "photo@example.com",
                "display_name": "Photo User",
                "photo_url": "https://example.com/photo.jpg",
            },
        )
        assert response.status_code == 201

    def test_create_user_duplicate_firebase_uid(self, client: TestClient) -> None:
        client.post(
            "/users",
            json={
                "firebase_uid": "api_uid_dup",
                "email": "dup1@example.com",
                "display_name": "Dup1",
            },
        )
        response = client.post(
            "/users",
            json={
                "firebase_uid": "api_uid_dup",
                "email": "dup2@example.com",
                "display_name": "Dup2",
            },
        )
        assert response.status_code == 409

    def test_create_user_invalid_email(self, client: TestClient) -> None:
        response = client.post(
            "/users",
            json={
                "firebase_uid": "api_uid_bad",
                "email": "not-an-email",
                "display_name": "Bad Email",
            },
        )
        assert response.status_code == 422

    def test_create_user_missing_fields(self, client: TestClient) -> None:
        response = client.post(
            "/users",
            json={"firebase_uid": "api_uid_missing"},
        )
        assert response.status_code == 422

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app as fastapi_app
import app.db.models  # noqa: F401

from tests.helpers.firebase_emulator import (
    clear_emulator_users,
    create_emulator_user,
)

engine = create_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture(autouse=True)
def _clean_emulator_users():
    """Clean up emulator users before each test."""
    clear_emulator_users()
    yield
    clear_emulator_users()


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


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


class TestAuthLogin:
    def test_login_creates_new_user(self, client: TestClient) -> None:
        emulator_resp = create_emulator_user("login_new@example.com")
        token = emulator_resp["idToken"]

        response = client.post(
            "/auth/login",
            json={"display_name": "New User", "photo_url": "https://example.com/photo.jpg"},
            headers=_auth_header(token),
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "login_new@example.com"
        assert data["display_name"] == "New User"
        assert data["photo_url"] == "https://example.com/photo.jpg"
        assert data["onboarding_completed"] is False

    def test_login_returns_existing_user(self, client: TestClient) -> None:
        emulator_resp = create_emulator_user("login_existing@example.com")
        token = emulator_resp["idToken"]

        resp1 = client.post(
            "/auth/login",
            json={"display_name": "First"},
            headers=_auth_header(token),
        )
        assert resp1.status_code == 200
        user_id = resp1.json()["id"]

        resp2 = client.post(
            "/auth/login",
            json={"display_name": "Second"},
            headers=_auth_header(token),
        )
        assert resp2.status_code == 200
        assert resp2.json()["id"] == user_id
        assert resp2.json()["display_name"] == "First"

    def test_login_without_token_returns_unauthorized(self, client: TestClient) -> None:
        response = client.post("/auth/login", json={})
        assert response.status_code in (401, 403)

    def test_login_with_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/auth/login",
            json={},
            headers=_auth_header("invalid-token"),
        )
        assert response.status_code == 401


class TestUsersMe:
    def test_get_me_returns_current_user(self, client: TestClient) -> None:
        emulator_resp = create_emulator_user("me@example.com")
        token = emulator_resp["idToken"]

        client.post(
            "/auth/login",
            json={"display_name": "Me User"},
            headers=_auth_header(token),
        )

        response = client.get("/users/me", headers=_auth_header(token))
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert data["display_name"] == "Me User"

    def test_get_me_without_registration_returns_404(self, client: TestClient) -> None:
        emulator_resp = create_emulator_user("unregistered@example.com")
        token = emulator_resp["idToken"]

        response = client.get("/users/me", headers=_auth_header(token))
        assert response.status_code == 404

    def test_get_me_without_token_returns_unauthorized(self, client: TestClient) -> None:
        response = client.get("/users/me")
        assert response.status_code in (401, 403)

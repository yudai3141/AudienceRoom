from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    def test_create_user(self, db: Session) -> None:
        repo = UserRepository(db)
        user = User(
            firebase_uid="uid_001",
            email="repo@example.com",
            display_name="Repo User",
        )
        created = repo.create_user(user)

        assert created.id is not None
        assert created.firebase_uid == "uid_001"
        assert created.email == "repo@example.com"
        assert created.display_name == "Repo User"
        assert created.onboarding_completed is False

    def test_get_user_by_id(self, db: Session) -> None:
        repo = UserRepository(db)
        user = User(
            firebase_uid="uid_002",
            email="byid@example.com",
            display_name="ById User",
        )
        created = repo.create_user(user)

        found = repo.get_user_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_user_by_id_not_found(self, db: Session) -> None:
        repo = UserRepository(db)
        found = repo.get_user_by_id(99999)
        assert found is None

    def test_get_user_by_firebase_uid(self, db: Session) -> None:
        repo = UserRepository(db)
        user = User(
            firebase_uid="uid_003",
            email="byuid@example.com",
            display_name="ByUid User",
        )
        repo.create_user(user)

        found = repo.get_user_by_firebase_uid("uid_003")
        assert found is not None
        assert found.firebase_uid == "uid_003"

    def test_get_user_by_firebase_uid_not_found(self, db: Session) -> None:
        repo = UserRepository(db)
        found = repo.get_user_by_firebase_uid("nonexistent")
        assert found is None

import pytest
from sqlalchemy.orm import Session

from app.services.user_service import UserService


class TestUserService:
    def test_create_user(self, db: Session) -> None:
        service = UserService(db)
        user = service.create_user(
            firebase_uid="svc_uid_001",
            email="svc@example.com",
            display_name="Svc User",
        )

        assert user.id is not None
        assert user.firebase_uid == "svc_uid_001"
        assert user.email == "svc@example.com"
        assert user.display_name == "Svc User"

    def test_create_user_duplicate_firebase_uid(self, db: Session) -> None:
        service = UserService(db)
        service.create_user(
            firebase_uid="svc_uid_dup",
            email="first@example.com",
            display_name="First",
        )

        with pytest.raises(ValueError, match="already exists"):
            service.create_user(
                firebase_uid="svc_uid_dup",
                email="second@example.com",
                display_name="Second",
            )

    def test_get_user(self, db: Session) -> None:
        service = UserService(db)
        created = service.create_user(
            firebase_uid="svc_uid_get",
            email="get@example.com",
            display_name="Get User",
        )

        found = service.get_user(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_user_not_found(self, db: Session) -> None:
        service = UserService(db)
        found = service.get_user(99999)
        assert found is None

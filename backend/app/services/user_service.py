from sqlalchemy.orm import Session

from app.db.models.user import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, db: Session) -> None:
        self._repository = UserRepository(db)

    def create_user(
        self,
        firebase_uid: str,
        email: str,
        display_name: str,
        photo_url: str | None = None,
    ) -> User:
        existing = self._repository.get_user_by_firebase_uid(firebase_uid)
        if existing is not None:
            raise ValueError(f"User with firebase_uid '{firebase_uid}' already exists")

        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
        )
        return self._repository.create_user(user)

    def get_or_create_user(
        self,
        firebase_uid: str,
        email: str,
        display_name: str | None = None,
        photo_url: str | None = None,
    ) -> tuple[User, bool]:
        """Return (user, created). If the user exists, return it; otherwise create."""
        existing = self._repository.get_user_by_firebase_uid(firebase_uid)
        if existing is not None:
            return existing, False

        user = User(
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name or email.split("@")[0],
            photo_url=photo_url,
        )
        return self._repository.create_user(user), True

    def get_user(self, user_id: int) -> User | None:
        return self._repository.get_user_by_id(user_id)

    def get_user_by_firebase_uid(self, firebase_uid: str) -> User | None:
        return self._repository.get_user_by_firebase_uid(firebase_uid)

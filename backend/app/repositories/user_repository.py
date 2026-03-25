from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.user import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create_user(self, user: User) -> User:
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id, User.deleted_at.is_(None))
        return self._db.execute(stmt).scalar_one_or_none()

    def get_user_by_firebase_uid(self, firebase_uid: str) -> User | None:
        stmt = select(User).where(
            User.firebase_uid == firebase_uid, User.deleted_at.is_(None)
        )
        return self._db.execute(stmt).scalar_one_or_none()

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from firebase_admin import auth
from sqlalchemy.orm import Session

from app.core.firebase import init_firebase
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.user_repository import UserRepository

security = HTTPBearer()  # Authorization: Bearer <token> を自動で取り出す

# Firebaseのトークンが正しいか確認する関数
def get_current_firebase_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Verify Firebase ID token and return decoded claims."""
    init_firebase()
    try:
        decoded = auth.verify_id_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )
    return decoded

# Firebaseユーザーに対応する自前DBのユーザーを取る関数
def get_current_user(
    decoded: dict = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> User:
    """Resolve Firebase UID to a DB user. 404 if not registered."""
    repo = UserRepository(db)
    user = repo.get_user_by_firebase_uid(decoded["uid"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registered",
        )
    return user

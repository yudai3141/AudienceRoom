from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_firebase_user
from app.db.session import get_db
from app.schemas.user import LoginRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse, status_code=200)
def login(
    body: LoginRequest,
    decoded: dict = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Verify Firebase token, get or create the user, and return profile."""
    service = UserService(db)
    user, _created = service.get_or_create_user(
        firebase_uid=decoded["uid"],
        email=decoded.get("email", ""),
        display_name=body.display_name,
        photo_url=body.photo_url,
    )
    return UserResponse.model_validate(user)

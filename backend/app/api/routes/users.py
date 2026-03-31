from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.practice_session import DashboardResponse
from app.schemas.user import UserCreateRequest, UserResponse
from app.services.practice_session_service import PracticeSessionService
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    body: UserCreateRequest,
    db: Session = Depends(get_db),
) -> UserResponse:
    service = UserService(db)
    try:
        user = service.create_user(
            firebase_uid=body.firebase_uid,
            email=body.email,
            display_name=body.display_name,
            photo_url=body.photo_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/me/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardResponse:
    service = PracticeSessionService(db)
    return service.get_dashboard(current_user.id)

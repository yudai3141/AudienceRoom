from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreateRequest, UserResponse
from app.services.user_service import UserService

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
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

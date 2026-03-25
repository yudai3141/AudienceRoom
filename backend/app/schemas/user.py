from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreateRequest(BaseModel):
    firebase_uid: str
    email: EmailStr
    display_name: str
    photo_url: str | None = None


class UserResponse(BaseModel):
    id: int
    firebase_uid: str
    email: str
    display_name: str
    photo_url: str | None
    onboarding_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Sent after Firebase client-side auth to register or retrieve the user."""
    display_name: str | None = None
    photo_url: str | None = None

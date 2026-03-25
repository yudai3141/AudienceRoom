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

    model_config = {"from_attributes": True}

from pydantic import BaseModel


class AiCharacterCreateRequest(BaseModel):
    code: str
    name: str
    role: str
    strictness: str
    personality: str | None = None
    voice_style: str | None = None
    description: str | None = None


class AiCharacterResponse(BaseModel):
    id: int
    code: str
    name: str
    role: str
    strictness: str
    personality: str | None
    voice_style: str | None
    description: str | None
    is_active: bool

    model_config = {"from_attributes": True}

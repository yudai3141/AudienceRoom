from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai_character import AiCharacterCreateRequest, AiCharacterResponse
from app.services.ai_character_service import AiCharacterService

router = APIRouter()


@router.post("/ai-characters", response_model=AiCharacterResponse, status_code=201)
def create_ai_character(
    body: AiCharacterCreateRequest,
    db: Session = Depends(get_db),
) -> AiCharacterResponse:
    service = AiCharacterService(db)
    try:
        character = service.create_character(
            code=body.code,
            name=body.name,
            role=body.role,
            strictness=body.strictness,
            personality=body.personality,
            voice_style=body.voice_style,
            description=body.description,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    return AiCharacterResponse.model_validate(character)


@router.get("/ai-characters", response_model=list[AiCharacterResponse])
def list_ai_characters(
    db: Session = Depends(get_db),
) -> list[AiCharacterResponse]:
    service = AiCharacterService(db)
    characters = service.list_active_characters()
    return [AiCharacterResponse.model_validate(c) for c in characters]


@router.get("/ai-characters/{character_id}", response_model=AiCharacterResponse)
def get_ai_character(
    character_id: int,
    db: Session = Depends(get_db),
) -> AiCharacterResponse:
    service = AiCharacterService(db)
    character = service.get_character(character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="AiCharacter not found")
    return AiCharacterResponse.model_validate(character)

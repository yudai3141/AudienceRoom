from sqlalchemy.orm import Session

from app.db.models.ai_character import AiCharacter
from app.repositories.ai_character_repository import AiCharacterRepository


class AiCharacterService:
    def __init__(self, db: Session) -> None:
        self._repository = AiCharacterRepository(db)

    def create_character(
        self,
        code: str,
        name: str,
        role: str,
        strictness: str,
        personality: str | None = None,
        voice_style: str | None = None,
        description: str | None = None,
    ) -> AiCharacter:
        existing = self._repository.get_by_code(code)
        if existing is not None:
            raise ValueError(f"AiCharacter with code '{code}' already exists")

        character = AiCharacter(
            code=code,
            name=name,
            role=role,
            strictness=strictness,
            personality=personality,
            voice_style=voice_style,
            description=description,
        )
        return self._repository.create(character)

    def get_character(self, character_id: int) -> AiCharacter | None:
        return self._repository.get_by_id(character_id)

    def list_active_characters(self) -> list[AiCharacter]:
        return self._repository.list_active()

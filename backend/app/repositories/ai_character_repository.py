from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.ai_character import AiCharacter


class AiCharacterRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, character: AiCharacter) -> AiCharacter:
        self._db.add(character)
        self._db.commit()
        self._db.refresh(character)
        return character

    def get_by_id(self, character_id: int) -> AiCharacter | None:
        stmt = select(AiCharacter).where(AiCharacter.id == character_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_by_code(self, code: str) -> AiCharacter | None:
        stmt = select(AiCharacter).where(AiCharacter.code == code)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_active(self) -> list[AiCharacter]:
        stmt = (
            select(AiCharacter)
            .where(AiCharacter.is_active.is_(True))
            .order_by(AiCharacter.id)
        )
        return list(self._db.execute(stmt).scalars().all())

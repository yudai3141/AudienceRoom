from sqlalchemy.orm import Session

from app.db.models.ai_character import AiCharacter
from app.repositories.ai_character_repository import AiCharacterRepository


class TestAiCharacterRepository:
    def test_create(self, db: Session) -> None:
        repo = AiCharacterRepository(db)
        character = AiCharacter(
            code="host_gentle_01",
            name="やさしい面接官",
            role="host",
            strictness="gentle",
        )
        created = repo.create(character)

        assert created.id is not None
        assert created.code == "host_gentle_01"
        assert created.is_active is True

    def test_get_by_id(self, db: Session) -> None:
        repo = AiCharacterRepository(db)
        character = AiCharacter(
            code="host_normal_01",
            name="普通の面接官",
            role="host",
            strictness="normal",
        )
        created = repo.create(character)

        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, db: Session) -> None:
        repo = AiCharacterRepository(db)
        assert repo.get_by_id(99999) is None

    def test_get_by_code(self, db: Session) -> None:
        repo = AiCharacterRepository(db)
        character = AiCharacter(
            code="aud_hard_01",
            name="厳しい聴衆",
            role="audience",
            strictness="hard",
        )
        repo.create(character)

        found = repo.get_by_code("aud_hard_01")
        assert found is not None
        assert found.name == "厳しい聴衆"

    def test_get_by_code_not_found(self, db: Session) -> None:
        repo = AiCharacterRepository(db)
        assert repo.get_by_code("nonexistent") is None

    def test_list_active(self, db: Session) -> None:
        repo = AiCharacterRepository(db)
        repo.create(AiCharacter(
            code="active_01", name="Active 1", role="host", strictness="gentle",
            is_active=True,
        ))
        repo.create(AiCharacter(
            code="inactive_01", name="Inactive 1", role="audience", strictness="normal",
            is_active=False,
        ))
        repo.create(AiCharacter(
            code="active_02", name="Active 2", role="audience", strictness="hard",
            is_active=True,
        ))

        active = repo.list_active()
        assert len(active) == 2
        assert all(c.is_active for c in active)

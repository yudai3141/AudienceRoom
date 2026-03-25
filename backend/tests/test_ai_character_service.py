import pytest
from sqlalchemy.orm import Session

from app.services.ai_character_service import AiCharacterService


class TestAiCharacterService:
    def test_create_character(self, db: Session) -> None:
        service = AiCharacterService(db)
        character = service.create_character(
            code="svc_host_01",
            name="テスト面接官",
            role="host",
            strictness="normal",
            personality="friendly",
        )

        assert character.id is not None
        assert character.code == "svc_host_01"
        assert character.personality == "friendly"

    def test_create_character_duplicate_code(self, db: Session) -> None:
        service = AiCharacterService(db)
        service.create_character(
            code="svc_dup", name="First", role="host", strictness="gentle",
        )

        with pytest.raises(ValueError, match="already exists"):
            service.create_character(
                code="svc_dup", name="Second", role="audience", strictness="hard",
            )

    def test_get_character(self, db: Session) -> None:
        service = AiCharacterService(db)
        created = service.create_character(
            code="svc_get_01", name="Get Test", role="host", strictness="gentle",
        )

        found = service.get_character(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_character_not_found(self, db: Session) -> None:
        service = AiCharacterService(db)
        assert service.get_character(99999) is None

    def test_list_active_characters(self, db: Session) -> None:
        service = AiCharacterService(db)
        service.create_character(
            code="svc_list_01", name="Active", role="host", strictness="normal",
        )

        active = service.list_active_characters()
        assert len(active) >= 1
        assert all(c.is_active for c in active)

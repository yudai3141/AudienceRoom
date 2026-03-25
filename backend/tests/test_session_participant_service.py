import pytest
from sqlalchemy.orm import Session

from app.db.models.ai_character import AiCharacter
from app.db.models.practice_session import PracticeSession
from app.db.models.user import User
from app.services.session_participant_service import SessionParticipantService


def _setup_prerequisites(db: Session) -> tuple[int, int]:
    user = User(
        firebase_uid="sp_svc_user",
        email="sp_svc@example.com",
        display_name="SP Svc User",
    )
    db.add(user)
    db.flush()

    session = PracticeSession(
        user_id=user.id, mode="presentation", participant_count=5,
    )
    db.add(session)
    db.flush()

    character = AiCharacter(
        code="sp_svc_char", name="テスト聴衆", role="audience", strictness="gentle",
    )
    db.add(character)
    db.flush()

    return session.id, character.id


class TestSessionParticipantService:
    def test_add_participant(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        service = SessionParticipantService(db)

        participant = service.add_participant(
            session_id=session_id,
            ai_character_id=character_id,
            display_name="サービス参加者",
            role="audience",
            seat_index=0,
        )

        assert participant.id is not None
        assert participant.role == "audience"

    def test_add_participant_invalid_role(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        service = SessionParticipantService(db)

        with pytest.raises(ValueError, match="Invalid role"):
            service.add_participant(
                session_id=session_id,
                ai_character_id=character_id,
                display_name="不正ロール",
                role="invalid",
                seat_index=0,
            )

    def test_add_participants_bulk(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        service = SessionParticipantService(db)

        items = [
            {
                "session_id": session_id,
                "ai_character_id": character_id,
                "display_name": f"一括{i}",
                "role": "audience",
                "seat_index": i,
            }
            for i in range(3)
        ]
        created = service.add_participants_bulk(items)
        assert len(created) == 3

    def test_add_participants_bulk_invalid_role(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        service = SessionParticipantService(db)

        items = [
            {
                "session_id": session_id,
                "ai_character_id": character_id,
                "display_name": "不正",
                "role": "invalid",
                "seat_index": 0,
            },
        ]
        with pytest.raises(ValueError, match="Invalid role"):
            service.add_participants_bulk(items)

    def test_get_participant(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        service = SessionParticipantService(db)

        created = service.add_participant(
            session_id=session_id,
            ai_character_id=character_id,
            display_name="取得テスト",
            role="host",
            seat_index=0,
        )

        found = service.get_participant(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_participant_not_found(self, db: Session) -> None:
        service = SessionParticipantService(db)
        assert service.get_participant(99999) is None

    def test_list_session_participants(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        service = SessionParticipantService(db)

        service.add_participant(
            session_id=session_id,
            ai_character_id=character_id,
            display_name="一覧1",
            role="host",
            seat_index=0,
        )
        service.add_participant(
            session_id=session_id,
            ai_character_id=character_id,
            display_name="一覧2",
            role="audience",
            seat_index=1,
        )

        participants = service.list_session_participants(session_id)
        assert len(participants) == 2

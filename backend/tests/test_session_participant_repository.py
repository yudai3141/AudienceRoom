from sqlalchemy.orm import Session

from app.db.models.ai_character import AiCharacter
from app.db.models.practice_session import PracticeSession
from app.db.models.session_participant import SessionParticipant
from app.db.models.user import User
from app.repositories.session_participant_repository import (
    SessionParticipantRepository,
)


def _setup_prerequisites(db: Session) -> tuple[int, int]:
    """Create user, session, and character, return (session_id, character_id)."""
    user = User(
        firebase_uid="sp_repo_user",
        email="sp_repo@example.com",
        display_name="SP Repo User",
    )
    db.add(user)
    db.flush()

    session = PracticeSession(
        user_id=user.id, mode="interview", participant_count=3,
    )
    db.add(session)
    db.flush()

    character = AiCharacter(
        code="sp_repo_char", name="テスト面接官", role="host", strictness="normal",
    )
    db.add(character)
    db.flush()

    return session.id, character.id


class TestSessionParticipantRepository:
    def test_create(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        repo = SessionParticipantRepository(db)

        participant = SessionParticipant(
            session_id=session_id,
            ai_character_id=character_id,
            display_name="面接官A",
            role="host",
            seat_index=0,
        )
        created = repo.create(participant)

        assert created.id is not None
        assert created.session_id == session_id
        assert created.ai_character_id == character_id
        assert created.is_active is True

    def test_bulk_create(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        repo = SessionParticipantRepository(db)

        participants = [
            SessionParticipant(
                session_id=session_id,
                ai_character_id=character_id,
                display_name=f"参加者{i}",
                role="audience",
                seat_index=i,
            )
            for i in range(3)
        ]
        created = repo.bulk_create(participants)

        assert len(created) == 3
        assert all(p.id is not None for p in created)

    def test_get_by_id(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        repo = SessionParticipantRepository(db)

        participant = SessionParticipant(
            session_id=session_id,
            ai_character_id=character_id,
            display_name="取得テスト",
            role="host",
            seat_index=0,
        )
        created = repo.create(participant)

        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_by_id_not_found(self, db: Session) -> None:
        repo = SessionParticipantRepository(db)
        assert repo.get_by_id(99999) is None

    def test_list_by_session_id(self, db: Session) -> None:
        session_id, character_id = _setup_prerequisites(db)
        repo = SessionParticipantRepository(db)

        for i in range(3):
            repo.create(SessionParticipant(
                session_id=session_id,
                ai_character_id=character_id,
                display_name=f"一覧テスト{i}",
                role="audience",
                seat_index=i,
            ))

        participants = repo.list_by_session_id(session_id)
        assert len(participants) == 3
        assert [p.seat_index for p in participants] == [0, 1, 2]

    def test_list_by_session_id_empty(self, db: Session) -> None:
        repo = SessionParticipantRepository(db)
        assert repo.list_by_session_id(99999) == []

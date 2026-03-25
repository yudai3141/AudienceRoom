import pytest
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.services.practice_session_service import PracticeSessionService


def _create_user(db: Session) -> User:
    user = User(
        firebase_uid="ps_svc_user",
        email="ps_svc@example.com",
        display_name="PS Svc User",
    )
    db.add(user)
    db.flush()
    return user


class TestPracticeSessionService:
    def test_create_session(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        session = service.create_session(
            user_id=user.id,
            mode="interview",
            participant_count=3,
            theme="エンジニア面接",
            target_context="interview",
        )

        assert session.id is not None
        assert session.status == "waiting"
        assert session.mode == "interview"
        assert session.theme == "エンジニア面接"

    def test_create_session_invalid_mode(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)

        with pytest.raises(ValueError, match="Invalid mode"):
            service.create_session(
                user_id=user.id, mode="invalid_mode", participant_count=1,
            )

    def test_get_session(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        created = service.create_session(
            user_id=user.id, mode="presentation", participant_count=5,
        )

        found = service.get_session(created.id)
        assert found is not None
        assert found.id == created.id

    def test_get_session_not_found(self, db: Session) -> None:
        service = PracticeSessionService(db)
        assert service.get_session(99999) is None

    def test_list_user_sessions(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        service.create_session(
            user_id=user.id, mode="interview", participant_count=2,
        )
        service.create_session(
            user_id=user.id, mode="free_conversation", participant_count=1,
        )

        sessions = service.list_user_sessions(user.id)
        assert len(sessions) == 2

    def test_update_status_waiting_to_active(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        created = service.create_session(
            user_id=user.id, mode="interview", participant_count=3,
        )

        updated = service.update_status(created.id, "active")
        assert updated.status == "active"
        assert updated.started_at is not None

    def test_update_status_active_to_completed(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        created = service.create_session(
            user_id=user.id, mode="interview", participant_count=3,
        )
        service.update_status(created.id, "active")

        updated = service.update_status(created.id, "completed")
        assert updated.status == "completed"
        assert updated.ended_at is not None

    def test_update_status_invalid_transition(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        created = service.create_session(
            user_id=user.id, mode="interview", participant_count=3,
        )

        with pytest.raises(ValueError, match="Cannot transition"):
            service.update_status(created.id, "completed")

    def test_update_status_invalid_status(self, db: Session) -> None:
        user = _create_user(db)
        service = PracticeSessionService(db)
        created = service.create_session(
            user_id=user.id, mode="interview", participant_count=3,
        )

        with pytest.raises(ValueError, match="Invalid status"):
            service.update_status(created.id, "unknown")

    def test_update_status_session_not_found(self, db: Session) -> None:
        service = PracticeSessionService(db)

        with pytest.raises(ValueError, match="not found"):
            service.update_status(99999, "active")

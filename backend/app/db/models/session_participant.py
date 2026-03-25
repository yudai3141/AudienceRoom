from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

PARTICIPANT_ROLES = ("host", "audience")


class SessionParticipant(Base):
    __tablename__ = "session_participants"
    __table_args__ = (
        CheckConstraint(
            f"role IN {PARTICIPANT_ROLES!r}",
            name="ck_session_participants_role",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("practice_sessions.id"), nullable=False
    )
    ai_character_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ai_characters.id"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    seat_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session = relationship("PracticeSession", backref="participants", lazy="select")
    ai_character = relationship("AiCharacter", lazy="select")

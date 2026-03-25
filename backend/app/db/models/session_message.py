from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SessionMessage(Base):
    __tablename__ = "session_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("practice_sessions.id"), nullable=False
    )
    participant_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("session_participants.id"), nullable=True
    )
    sequence_no: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    transcript_confidence: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 3), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    session = relationship("PracticeSession", backref="messages", lazy="select")
    participant = relationship("SessionParticipant", lazy="select")

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

SESSION_STATUSES = ("waiting", "active", "completed", "cancelled", "error")
SESSION_MODES = ("presentation", "interview", "free_conversation")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    __table_args__ = (
        CheckConstraint(
            f"status IN {SESSION_STATUSES!r}",
            name="ck_practice_sessions_status",
        ),
        CheckConstraint(
            f"mode IN {SESSION_MODES!r}",
            name="ck_practice_sessions_mode",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="waiting", server_default="waiting"
    )
    mode: Mapped[str] = mapped_column(String(30), nullable=False)
    participant_count: Mapped[int] = mapped_column(Integer, nullable=False)
    feedback_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    theme: Mapped[str | None] = mapped_column(Text, nullable=True)
    presentation_duration_sec: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    presentation_qa_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_concerns: Mapped[str | None] = mapped_column(Text, nullable=True)
    session_brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_context: Mapped[str | None] = mapped_column(String(50), nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    feedback_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user = relationship("User", backref="practice_sessions", lazy="select")

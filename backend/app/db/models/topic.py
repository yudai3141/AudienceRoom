from datetime import datetime

from sqlalchemy import (
    BigInteger,
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

TOPIC_STATUSES = ("active", "archived")


class Topic(Base):
    """面接で話すエピソードを育てる永続単位 (記憶層の中心)。

    `practice_sessions` が 1 回きりの揮発的な練習なのに対し、`topics` は
    練習をまたいで情報が育つ。詳細は backend/docs/db-schema-plan-b-topics.md。
    """

    __tablename__ = "topics"
    __table_args__ = (
        CheckConstraint(
            f"status IN {TOPIC_STATUSES!r}",
            name="ck_topics_status",
        ),
        CheckConstraint(
            "completeness_score >= 0 AND completeness_score <= 100",
            name="ck_topics_completeness_score",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", server_default="active"
    )
    # AI が練習後に更新する非導出値 (0-100)。未評価のときは NULL。
    completeness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # トピック全体のドキュメント要約 (最新)。
    current_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
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

    user = relationship("User", backref="topics", lazy="select")
    nodes = relationship(
        "TopicNode",
        back_populates="topic",
        lazy="select",
        cascade="all, delete-orphan",
    )
    edges = relationship(
        "TopicEdge",
        back_populates="topic",
        lazy="select",
        cascade="all, delete-orphan",
    )

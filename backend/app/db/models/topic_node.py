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

TOPIC_NODE_COVERAGES = ("covered", "weak", "gap")


class TopicNode(Base):
    """トピックを構成する論点・要素 (仮想 GraphRAG のノード)。

    `coverage` が「話せる / 弱い / 空き」を表し、可視化の塗り分け・弱点数の集計・
    質問生成でのノード選択に使う。`node_type` はタクソノミー未確定のため
    CHECK を付けず自由記述とする (詳細: db-schema-plan-b-topics.md)。
    """

    __tablename__ = "topic_nodes"
    __table_args__ = (
        CheckConstraint(
            f"coverage IN {TOPIC_NODE_COVERAGES!r}",
            name="ck_topic_nodes_coverage",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topics.id"), nullable=False
    )
    # 自由記述 (theme/method/strength/weakness ...)。タクソノミー確定後に CHECK を付ける。
    node_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    coverage: Mapped[str] = mapped_column(
        String(20), nullable=False, default="gap", server_default="gap"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
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

    topic = relationship("Topic", back_populates="nodes", lazy="select")

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TopicEdge(Base):
    """トピック内のノード間の有向関係 (仮想 GraphRAG のエッジ)。

    `relation_type` は自由記述。`contradicts` で矛盾を矛盾のまま保持し、
    面接官が突く的にする。「接続の弱さ」は事前計算せず質問生成時に LLM が判断する
    (詳細: db-schema-plan-b-topics.md)。
    """

    __tablename__ = "topic_edges"
    __table_args__ = (
        UniqueConstraint(
            "source_node_id",
            "target_node_id",
            "relation_type",
            name="uq_topic_edges_src_tgt_rel",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topics.id"), nullable=False
    )
    source_node_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topic_nodes.id"), nullable=False
    )
    target_node_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topic_nodes.id"), nullable=False
    )
    # 自由記述 (leads_to/addresses/contradicts ...)。タクソノミー確定後に CHECK を付ける。
    relation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    topic = relationship("Topic", back_populates="edges", lazy="select")

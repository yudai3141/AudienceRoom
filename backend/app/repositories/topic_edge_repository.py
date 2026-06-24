from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.models.topic_edge import TopicEdge


class TopicEdgeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, edge: TopicEdge) -> TopicEdge:
        self._db.add(edge)
        self._db.commit()
        self._db.refresh(edge)
        return edge

    def get_by_id(self, edge_id: int) -> TopicEdge | None:
        stmt = select(TopicEdge).where(TopicEdge.id == edge_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_topic_id(self, topic_id: int) -> list[TopicEdge]:
        """トピックの全エッジ。グラフ描画・コンテキスト構築に使う。"""
        stmt = (
            select(TopicEdge)
            .where(TopicEdge.topic_id == topic_id)
            .order_by(TopicEdge.id)
        )
        return list(self._db.execute(stmt).scalars().all())

    def list_by_node_id(self, node_id: int) -> list[TopicEdge]:
        """あるノードに接続するエッジ (source/target 両方)。1-hop 近傍の取得に使う。"""
        stmt = select(TopicEdge).where(
            or_(
                TopicEdge.source_node_id == node_id,
                TopicEdge.target_node_id == node_id,
            )
        )
        return list(self._db.execute(stmt).scalars().all())

    def find(
        self, source_node_id: int, target_node_id: int, relation_type: str
    ) -> TopicEdge | None:
        """同一エッジの存在確認 (upsert 時の重複回避に使う)。"""
        stmt = select(TopicEdge).where(
            TopicEdge.source_node_id == source_node_id,
            TopicEdge.target_node_id == target_node_id,
            TopicEdge.relation_type == relation_type,
        )
        return self._db.execute(stmt).scalar_one_or_none()

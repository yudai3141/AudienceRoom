from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode

WEAK_COVERAGES = ("gap", "weak")


class TopicNodeRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, node: TopicNode) -> TopicNode:
        self._db.add(node)
        self._db.commit()
        self._db.refresh(node)
        return node

    def bulk_create(self, nodes: list[TopicNode]) -> list[TopicNode]:
        self._db.add_all(nodes)
        self._db.commit()
        for node in nodes:
            self._db.refresh(node)
        return nodes

    def get_by_id(self, node_id: int) -> TopicNode | None:
        stmt = select(TopicNode).where(TopicNode.id == node_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def list_by_topic_id(self, topic_id: int) -> list[TopicNode]:
        """トピックの全ノード (表示順)。グラフ描画・コンテキスト構築に使う。"""
        stmt = (
            select(TopicNode)
            .where(TopicNode.topic_id == topic_id)
            .order_by(TopicNode.sort_order, TopicNode.id)
        )
        return list(self._db.execute(stmt).scalars().all())

    def list_candidate_nodes(
        self, topic_id: int, *, limit: int = 8
    ) -> list[TopicNode]:
        """仮想 GraphRAG の質問対象候補。

        `coverage` が gap/weak のノード、または contradicts エッジに関与する
        ノードを返す。最終的にどれを聞くかは service 層が LLM に選ばせる。
        """
        contradiction_node_ids = (
            select(TopicEdge.source_node_id)
            .where(
                TopicEdge.topic_id == topic_id,
                TopicEdge.relation_type == "contradicts",
            )
            .union(
                select(TopicEdge.target_node_id).where(
                    TopicEdge.topic_id == topic_id,
                    TopicEdge.relation_type == "contradicts",
                )
            )
        )
        stmt = (
            select(TopicNode)
            .where(
                TopicNode.topic_id == topic_id,
                or_(
                    TopicNode.coverage.in_(WEAK_COVERAGES),
                    TopicNode.id.in_(contradiction_node_ids),
                ),
            )
            .order_by(TopicNode.sort_order, TopicNode.id)
            .limit(limit)
        )
        return list(self._db.execute(stmt).scalars().all())

    def count_weak_by_topic_id(self, topic_id: int) -> int:
        """まだ弱い論点 (coverage=gap/weak) の数。ダッシュボードの「弱点数」に使う。"""
        stmt = (
            select(func.count())
            .select_from(TopicNode)
            .where(
                TopicNode.topic_id == topic_id,
                TopicNode.coverage.in_(WEAK_COVERAGES),
            )
        )
        return self._db.execute(stmt).scalar_one()

    def update(self, node: TopicNode) -> TopicNode:
        self._db.commit()
        self._db.refresh(node)
        return node

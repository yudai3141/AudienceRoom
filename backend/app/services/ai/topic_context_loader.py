from sqlalchemy.orm import Session

from app.repositories.topic_edge_repository import TopicEdgeRepository
from app.repositories.topic_node_repository import TopicNodeRepository
from app.services.prompts.topic_context import build_topic_memory_context


def load_topic_memory_context(db: Session, topic_id: int | None) -> str | None:
    """セッションのトピックグラフを読み込み、プロンプト注入用テキストを返す。

    会話サービスが「覚えている＋深掘り」を実現するための仮想 GraphRAG の
    retrieve 部分。topic_id が無い・グラフが空なら None。
    """
    if topic_id is None:
        return None
    nodes = TopicNodeRepository(db).list_by_topic_id(topic_id)
    edges = TopicEdgeRepository(db).list_by_topic_id(topic_id)
    return build_topic_memory_context(nodes, edges)

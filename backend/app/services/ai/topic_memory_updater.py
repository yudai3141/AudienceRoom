import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.db.models.topic_node import TopicNode
from app.repositories.practice_session_repository import PracticeSessionRepository
from app.repositories.session_message_repository import SessionMessageRepository
from app.repositories.topic_edge_repository import TopicEdgeRepository
from app.repositories.topic_node_repository import TopicNodeRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.llm import get_llm_provider
from app.services.ai.llm.base import LLMProvider
from app.services.ai.topic_graph_service import TopicGraphService
from app.services.prompts.topic_session_update import build_topic_session_update_prompt

logger = logging.getLogger(__name__)


def compute_completeness(nodes: list[TopicNode]) -> int | None:
    """coverage 比から完成度(0-100)を算出する。ノードが無ければ None。

    completeness = covered ノード数 / 全ノード数 * 100（四捨五入）。
    deterministic で説明可能（weak/gap が減るほど上がる）。
    """
    if not nodes:
        return None
    covered = sum(1 for n in nodes if n.coverage == "covered")
    return round(covered / len(nodes) * 100)


@dataclass
class TopicUpdateResult:
    skipped: bool = False
    topic_id: int | None = None
    created_nodes: list[TopicNode] = field(default_factory=list)
    updated_nodes: list[TopicNode] = field(default_factory=list)
    created_edges: list = field(default_factory=list)
    coverage_changes: list[dict] = field(default_factory=list)
    completeness_before: int | None = None
    completeness_after: int | None = None
    current_summary: str | None = None


class TopicMemoryUpdater:
    """練習後に会話全体からトピックグラフを 1 回だけ更新する（仮想 GraphRAG の write）。

    LLM 呼び出し（抽出）と純粋な DB 更新（TopicGraphService.apply_graph_delta）を
    組み合わせる。完成度は coverage 比から決定論的に算出し、要約のみ LLM が生成する。
    """

    def __init__(self, db: Session, llm: LLMProvider | None = None) -> None:
        self._db = db
        self._session_repo = PracticeSessionRepository(db)
        self._message_repo = SessionMessageRepository(db)
        self._topic_repo = TopicRepository(db)
        self._node_repo = TopicNodeRepository(db)
        self._edge_repo = TopicEdgeRepository(db)
        self._llm = llm or get_llm_provider()
        self._graph = TopicGraphService(db, llm=self._llm)

    async def update_from_session(self, session_id: int) -> TopicUpdateResult:
        session = self._session_repo.get_by_id(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found")

        if session.topic_id is None:
            # トピックに紐づかない練習は更新対象外
            return TopicUpdateResult(skipped=True)

        topic = self._topic_repo.get_by_id(session.topic_id)
        if topic is None:
            raise ValueError(f"Topic {session.topic_id} not found")

        messages = self._message_repo.list_by_session_id(session_id)
        conversation_log = [
            {
                "role": "assistant" if m.participant_id else "user",
                "content": m.content,
            }
            for m in messages
        ]

        nodes_before = self._node_repo.list_by_topic_id(topic.id)
        edges_before = self._edge_repo.list_by_topic_id(topic.id)
        coverage_before = {n.label: n.coverage for n in nodes_before}
        completeness_before = topic.completeness_score

        prompt = build_topic_session_update_prompt(
            topic_title=topic.title,
            graph_context=TopicGraphService._serialize_graph(nodes_before, edges_before),
            conversation_log=conversation_log,
        )
        try:
            data = await self._llm.generate_json(prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Topic memory update extraction failed: {e}")
            raise ValueError(f"Failed to update topic memory: {e}") from e

        delta = {
            "nodes": data.get("nodes", []) or [],
            "edges": data.get("edges", []) or [],
        }
        graph_result = self._graph.apply_graph_delta(topic.id, delta)

        nodes_after = self._node_repo.list_by_topic_id(topic.id)
        completeness_after = compute_completeness(nodes_after)
        summary = data.get("current_summary") or topic.current_summary

        topic.completeness_score = completeness_after
        topic.current_summary = summary
        self._topic_repo.update(topic)

        coverage_changes = []
        for n in nodes_after:
            prev = coverage_before.get(n.label)
            if prev is None:
                coverage_changes.append({"label": n.label, "before": None, "after": n.coverage})
            elif prev != n.coverage:
                coverage_changes.append({"label": n.label, "before": prev, "after": n.coverage})

        return TopicUpdateResult(
            skipped=False,
            topic_id=topic.id,
            created_nodes=graph_result.created_nodes,
            updated_nodes=graph_result.updated_nodes,
            created_edges=graph_result.created_edges,
            coverage_changes=coverage_changes,
            completeness_before=completeness_before,
            completeness_after=completeness_after,
            current_summary=summary,
        )

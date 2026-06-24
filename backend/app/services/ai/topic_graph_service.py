import logging
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TOPIC_NODE_COVERAGES, TopicNode
from app.repositories.topic_edge_repository import TopicEdgeRepository
from app.repositories.topic_node_repository import TopicNodeRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.llm import get_llm_provider
from app.services.ai.llm.base import LLMProvider
from app.services.prompts.topic_extract import build_topic_extract_prompt
from app.services.prompts.topic_question import build_topic_question_prompt

logger = logging.getLogger(__name__)

DEFAULT_NEW_NODE_COVERAGE = "weak"


@dataclass
class QuestionResult:
    """質問生成の結果。question が None のときは候補が無い (一般質問にフォールバック)。"""

    question: str | None
    node_id: int | None
    rationale: str | None


@dataclass
class GraphDeltaResult:
    created_nodes: list[TopicNode] = field(default_factory=list)
    updated_nodes: list[TopicNode] = field(default_factory=list)
    created_edges: list[TopicEdge] = field(default_factory=list)


class TopicGraphService:
    """仮想 GraphRAG: トピックグラフを使った質問生成と、回答からのグラフ更新。

    LLM 呼び出し (generate_question / ingest_answer) と純粋な DB 更新
    (apply_graph_delta) を分離し、後者を LLM なしでテストできるようにしている。
    """

    def __init__(self, db: Session, llm: LLMProvider | None = None) -> None:
        self._db = db
        self._topic_repo = TopicRepository(db)
        self._node_repo = TopicNodeRepository(db)
        self._edge_repo = TopicEdgeRepository(db)
        self._llm = llm or get_llm_provider()

    # ------------------------------------------------------------------ #
    # 質問生成
    # ------------------------------------------------------------------ #
    async def generate_question(
        self, topic_id: int, conversation_history: list[dict] | None = None
    ) -> QuestionResult:
        topic = self._topic_repo.get_by_id(topic_id)
        if topic is None:
            raise ValueError(f"Topic with id {topic_id} not found")

        candidates = self._node_repo.list_candidate_nodes(topic_id)
        if not candidates:
            # グラフが空、または弱点/矛盾が無い → 呼び出し側が一般質問へフォールバック
            return QuestionResult(question=None, node_id=None, rationale=None)

        nodes = self._node_repo.list_by_topic_id(topic_id)
        edges = self._edge_repo.list_by_topic_id(topic_id)
        prompt = build_topic_question_prompt(
            topic_title=topic.title,
            graph_context=self._serialize_graph(nodes, edges),
            candidates=[
                {
                    "id": c.id,
                    "label": c.label,
                    "coverage": c.coverage,
                    "node_type": c.node_type,
                }
                for c in candidates
            ],
            conversation_history=conversation_history or [],
        )

        data = await self._llm.generate_json(prompt, temperature=0.7)

        question = data.get("question")
        if not question:
            raise ValueError("LLM did not return a question")

        candidate_ids = {c.id for c in candidates}
        node_id = data.get("selected_node_id")
        if node_id not in candidate_ids:
            # LLM が候補外を返したら最初の候補に寄せる (grounding を保つ)
            node_id = candidates[0].id

        return QuestionResult(
            question=question,
            node_id=node_id,
            rationale=data.get("rationale"),
        )

    # ------------------------------------------------------------------ #
    # 回答からのグラフ更新
    # ------------------------------------------------------------------ #
    async def ingest_answer(
        self, topic_id: int, answer: str, question: str | None = None
    ) -> GraphDeltaResult:
        topic = self._topic_repo.get_by_id(topic_id)
        if topic is None:
            raise ValueError(f"Topic with id {topic_id} not found")

        nodes = self._node_repo.list_by_topic_id(topic_id)
        edges = self._edge_repo.list_by_topic_id(topic_id)
        prompt = build_topic_extract_prompt(
            topic_title=topic.title,
            graph_context=self._serialize_graph(nodes, edges),
            question=question,
            answer=answer,
        )

        try:
            delta = await self._llm.generate_json(prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Topic graph extraction failed: {e}")
            raise ValueError(f"Failed to extract topic graph: {e}") from e

        return self.apply_graph_delta(topic_id, delta)

    def apply_graph_delta(self, topic_id: int, delta: dict) -> GraphDeltaResult:
        """LLM が抽出したグラフ差分を upsert する (純粋な DB 操作)。

        - 既存 label に一致 → 更新（detail / coverage）
        - 新規 label → 新ノード作成
        - エッジは label を id に解決し、重複は作らない（contradicts もここを通る）
        """
        result = GraphDeltaResult()
        label_to_node = {n.label: n for n in self._node_repo.list_by_topic_id(topic_id)}

        for nd in delta.get("nodes", []) or []:
            label = (nd.get("label") or "").strip()
            if not label:
                continue
            coverage = nd.get("coverage")
            coverage = coverage if coverage in TOPIC_NODE_COVERAGES else None
            existing = label_to_node.get(label)
            if existing is not None:
                if nd.get("detail"):
                    existing.detail = nd["detail"]
                if coverage is not None:
                    existing.coverage = coverage
                self._node_repo.update(existing)
                result.updated_nodes.append(existing)
            else:
                node = TopicNode(
                    topic_id=topic_id,
                    label=label,
                    node_type=nd.get("node_type"),
                    detail=nd.get("detail"),
                    coverage=coverage or DEFAULT_NEW_NODE_COVERAGE,
                )
                self._node_repo.create(node)
                label_to_node[label] = node
                result.created_nodes.append(node)

        for ed in delta.get("edges", []) or []:
            source = label_to_node.get((ed.get("source") or "").strip())
            target = label_to_node.get((ed.get("target") or "").strip())
            relation = (ed.get("relation_type") or "").strip()
            if source is None or target is None or not relation:
                continue
            if source.id == target.id:
                continue
            if self._edge_repo.find(source.id, target.id, relation) is not None:
                continue
            edge = TopicEdge(
                topic_id=topic_id,
                source_node_id=source.id,
                target_node_id=target.id,
                relation_type=relation,
            )
            self._edge_repo.create(edge)
            result.created_edges.append(edge)

        return result

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _serialize_graph(nodes: list[TopicNode], edges: list[TopicEdge]) -> str:
        id_to_label = {n.id: n.label for n in nodes}
        lines = ["[ノード]"]
        if not nodes:
            lines.append("(なし)")
        for n in nodes:
            detail = f" — {n.detail}" if n.detail else ""
            lines.append(f"- id={n.id} [{n.coverage}] {n.label}{detail}")
        lines.append("[関係]")
        if not edges:
            lines.append("(なし)")
        for e in edges:
            src = id_to_label.get(e.source_node_id, "?")
            tgt = id_to_label.get(e.target_node_id, "?")
            lines.append(f"- {src} --{e.relation_type}--> {tgt}")
        return "\n".join(lines)

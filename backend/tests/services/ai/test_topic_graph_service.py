"""TopicGraphService (仮想 GraphRAG) のテスト (Plan B Phase B-1)。

LLM はモック注入し、グラフ更新ロジック (apply_graph_delta) は LLM なしで検証する。
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.db.models.topic import Topic
from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode
from app.db.models.user import User
from app.repositories.topic_edge_repository import TopicEdgeRepository
from app.repositories.topic_node_repository import TopicNodeRepository
from app.repositories.topic_repository import TopicRepository
from app.services.ai.topic_graph_service import TopicGraphService


def _seed_topic(db: Session, suffix: str = "") -> Topic:
    user = User(
        firebase_uid=f"graph_user{suffix}",
        email=f"graph{suffix}@example.com",
        display_name="Graph User",
    )
    db.add(user)
    db.flush()
    return TopicRepository(db).create(Topic(user_id=user.id, title="研究内容"))


def _service(db: Session, json_return: dict | None = None):
    llm = MagicMock()
    llm.generate_json = AsyncMock(return_value=json_return or {})
    return TopicGraphService(db, llm=llm), llm


class TestApplyGraphDelta:
    def test_creates_nodes_and_edges(self, db: Session) -> None:
        topic = _seed_topic(db)
        svc, _ = _service(db)
        delta = {
            "nodes": [
                {"label": "手法", "coverage": "covered"},
                {"label": "成果", "coverage": "weak"},
            ],
            "edges": [{"source": "手法", "target": "成果", "relation_type": "leads_to"}],
        }
        result = svc.apply_graph_delta(topic.id, delta)

        assert len(result.created_nodes) == 2
        assert len(result.created_edges) == 1
        labels = {n.label for n in TopicNodeRepository(db).list_by_topic_id(topic.id)}
        assert labels == {"手法", "成果"}

    def test_updates_existing_node_by_label(self, db: Session) -> None:
        topic = _seed_topic(db)
        node_repo = TopicNodeRepository(db)
        node_repo.create(TopicNode(topic_id=topic.id, label="評価方法", coverage="gap"))
        svc, _ = _service(db)

        result = svc.apply_graph_delta(
            topic.id,
            {"nodes": [{"label": "評価方法", "detail": "定量評価した", "coverage": "covered"}]},
        )

        assert len(result.created_nodes) == 0
        assert len(result.updated_nodes) == 1
        refreshed = node_repo.list_by_topic_id(topic.id)
        assert len(refreshed) == 1
        assert refreshed[0].coverage == "covered"
        assert refreshed[0].detail == "定量評価した"

    def test_new_node_defaults_coverage_when_invalid(self, db: Session) -> None:
        topic = _seed_topic(db)
        svc, _ = _service(db)
        svc.apply_graph_delta(topic.id, {"nodes": [{"label": "x", "coverage": "bogus"}]})
        node = TopicNodeRepository(db).list_by_topic_id(topic.id)[0]
        assert node.coverage == "weak"  # DEFAULT_NEW_NODE_COVERAGE

    def test_skips_duplicate_edge(self, db: Session) -> None:
        topic = _seed_topic(db)
        node_repo = TopicNodeRepository(db)
        a = node_repo.create(TopicNode(topic_id=topic.id, label="手法"))
        b = node_repo.create(TopicNode(topic_id=topic.id, label="成果"))
        TopicEdgeRepository(db).create(
            TopicEdge(topic_id=topic.id, source_node_id=a.id, target_node_id=b.id, relation_type="leads_to")
        )
        svc, _ = _service(db)
        result = svc.apply_graph_delta(
            topic.id,
            {"edges": [{"source": "手法", "target": "成果", "relation_type": "leads_to"}]},
        )
        assert len(result.created_edges) == 0

    def test_skips_self_loop_and_unknown_labels(self, db: Session) -> None:
        topic = _seed_topic(db)
        TopicNodeRepository(db).create(TopicNode(topic_id=topic.id, label="手法"))
        svc, _ = _service(db)
        result = svc.apply_graph_delta(
            topic.id,
            {
                "edges": [
                    {"source": "手法", "target": "手法", "relation_type": "leads_to"},
                    {"source": "手法", "target": "存在しない", "relation_type": "leads_to"},
                    {"source": "手法", "target": "成果", "relation_type": ""},
                ]
            },
        )
        assert len(result.created_edges) == 0

    def test_contradiction_kept_as_edge(self, db: Session) -> None:
        topic = _seed_topic(db)
        TopicNodeRepository(db).create(
            TopicNode(topic_id=topic.id, label="主導した", coverage="covered")
        )
        svc, _ = _service(db)
        result = svc.apply_graph_delta(
            topic.id,
            {
                "nodes": [{"label": "チームで決めた", "coverage": "covered"}],
                "edges": [{"source": "主導した", "target": "チームで決めた", "relation_type": "contradicts"}],
            },
        )
        assert len(result.created_edges) == 1
        edges = TopicEdgeRepository(db).list_by_topic_id(topic.id)
        assert edges[0].relation_type == "contradicts"


class TestGenerateQuestion:
    async def test_empty_graph_returns_none(self, db: Session) -> None:
        topic = _seed_topic(db)
        svc, llm = _service(db)
        result = await svc.generate_question(topic.id)
        assert result.question is None
        llm.generate_json.assert_not_awaited()

    async def test_returns_question_with_valid_node(self, db: Session) -> None:
        topic = _seed_topic(db)
        node = TopicNodeRepository(db).create(
            TopicNode(topic_id=topic.id, label="評価方法", coverage="weak")
        )
        svc, _ = _service(
            db,
            {"selected_node_id": node.id, "question": "評価方法は？", "rationale": "弱いから"},
        )
        result = await svc.generate_question(topic.id, conversation_history=[])
        assert result.question == "評価方法は？"
        assert result.node_id == node.id
        assert result.rationale == "弱いから"

    async def test_out_of_candidate_node_falls_back(self, db: Session) -> None:
        topic = _seed_topic(db)
        node = TopicNodeRepository(db).create(
            TopicNode(topic_id=topic.id, label="評価方法", coverage="weak")
        )
        svc, _ = _service(
            db, {"selected_node_id": 999999, "question": "Q", "rationale": "r"}
        )
        result = await svc.generate_question(topic.id)
        assert result.node_id == node.id  # 候補外 → 最初の候補に寄せる


class TestIngestAnswer:
    async def test_ingests_and_applies_delta(self, db: Session) -> None:
        topic = _seed_topic(db)
        svc, llm = _service(
            db,
            {"nodes": [{"label": "評価方法", "coverage": "weak"}], "edges": []},
        )
        result = await svc.ingest_answer(topic.id, "定量的に評価しました", question="評価は？")
        llm.generate_json.assert_awaited_once()
        assert len(result.created_nodes) == 1
        assert TopicNodeRepository(db).list_by_topic_id(topic.id)[0].label == "評価方法"

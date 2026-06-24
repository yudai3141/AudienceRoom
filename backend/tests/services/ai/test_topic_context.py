"""トピック記憶のプロンプト注入 (純粋関数) のテスト。"""
from app.db.models.topic_edge import TopicEdge
from app.db.models.topic_node import TopicNode
from app.services.prompts.interview import build_interview_prompt
from app.services.prompts.topic_context import build_topic_memory_context


def _node(id: int, label: str, coverage: str = "gap", detail: str | None = None) -> TopicNode:
    n = TopicNode(topic_id=1, label=label, coverage=coverage, detail=detail)
    n.id = id
    return n


class TestBuildTopicMemoryContext:
    def test_empty_returns_none(self) -> None:
        assert build_topic_memory_context([], []) is None

    def test_includes_coverage_and_edges(self) -> None:
        a = _node(1, "手法", coverage="covered")
        b = _node(2, "評価方法", coverage="weak", detail="抽象的")
        edge = TopicEdge(topic_id=1, source_node_id=1, target_node_id=2, relation_type="contradicts")
        text = build_topic_memory_context([a, b], [edge])

        assert text is not None
        assert "[covered] 手法" in text
        assert "[weak] 評価方法 — 抽象的" in text
        assert "手法 --contradicts--> 評価方法" in text


class TestInterviewPromptInjection:
    def test_topic_context_injected(self) -> None:
        messages = build_interview_prompt(
            theme=None,
            user_goal=None,
            user_concerns=None,
            strictness="normal",
            character_name="面接官",
            conversation_history=[],
            topic_context="【このトピックで過去に話した内容（あなたの記憶）】\n- [weak] 評価方法",
        )
        system = messages[0].content
        assert "過去に話した内容" in system
        assert "評価方法" in system

    def test_no_topic_context_no_memory_block(self) -> None:
        messages = build_interview_prompt(
            theme=None,
            user_goal=None,
            user_concerns=None,
            strictness="normal",
            character_name="面接官",
            conversation_history=[],
        )
        assert "過去に話した内容" not in messages[0].content

"""GraphRAG プロンプトの回帰テスト。

LLM プロバイダ (Gemini 等) は user メッセージを最低 1 つ要求するため、
system だけのプロンプトにならないことを保証する。
"""
from app.services.prompts.topic_extract import build_topic_extract_prompt
from app.services.prompts.topic_question import build_topic_question_prompt


def _roles(messages) -> list[str]:
    return [m.role for m in messages]


class TestTopicPromptsHaveUserMessage:
    def test_question_prompt_has_user_message(self) -> None:
        messages = build_topic_question_prompt(
            topic_title="研究内容",
            graph_context="[ノード]\n- id=1 [weak] 評価方法",
            candidates=[{"id": 1, "label": "評価方法", "coverage": "weak", "node_type": None}],
            conversation_history=[],
        )
        assert "user" in _roles(messages)

    def test_extract_prompt_has_user_message_with_answer(self) -> None:
        messages = build_topic_extract_prompt(
            topic_title="研究内容",
            graph_context="[ノード]\n- id=1 [weak] 評価方法",
            question="評価方法は？",
            answer="再現精度を15%改善しました",
        )
        assert "user" in _roles(messages)
        user_content = " ".join(m.content for m in messages if m.role == "user")
        assert "再現精度を15%改善しました" in user_content

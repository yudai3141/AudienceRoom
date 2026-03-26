import pytest

from app.services.prompts.feedback import build_feedback_prompt
from app.services.prompts.interview import build_interview_prompt
from app.services.prompts.presentation import build_presentation_prompt


class TestFeedbackPrompt:
    def test_build_feedback_prompt_basic(self):
        messages = build_feedback_prompt(
            mode="interview",
            theme="エンジニア面接",
            user_goal="自己PRを改善したい",
            user_concerns="緊張しやすい",
            conversation_log=[
                {"role": "user", "content": "私の強みは問題解決能力です"},
                {"role": "assistant", "content": "具体的な例を教えてください"},
            ],
        )

        assert len(messages) == 2
        assert messages[0].role == "system"
        assert messages[1].role == "user"
        assert "面接練習" in messages[0].content
        assert "JSON" in messages[0].content
        assert "エンジニア面接" in messages[1].content

    def test_build_feedback_prompt_without_optional_fields(self):
        messages = build_feedback_prompt(
            mode="presentation",
            theme=None,
            user_goal=None,
            user_concerns=None,
            conversation_log=[
                {"role": "user", "content": "本日は新製品についてお話しします"},
            ],
        )

        assert len(messages) == 2
        assert "プレゼン練習" in messages[0].content


class TestInterviewPrompt:
    def test_build_interview_prompt_basic(self):
        messages = build_interview_prompt(
            theme="営業職の面接",
            user_goal="志望動機をうまく伝えたい",
            user_concerns="質問に詰まることがある",
            strictness="normal",
            character_name="田中面接官",
            conversation_history=[],
        )

        assert len(messages) == 1
        assert messages[0].role == "system"
        assert "田中面接官" in messages[0].content
        assert "営業職の面接" in messages[0].content

    def test_build_interview_prompt_with_history(self):
        messages = build_interview_prompt(
            theme="エンジニア面接",
            user_goal=None,
            user_concerns=None,
            strictness="hard",
            character_name="佐藤面接官",
            conversation_history=[
                {"role": "assistant", "content": "自己紹介をお願いします"},
                {"role": "user", "content": "山田太郎と申します"},
            ],
        )

        assert len(messages) == 3
        assert messages[0].role == "system"
        assert messages[1].role == "assistant"
        assert messages[2].role == "user"
        assert "厳しめ" in messages[0].content

    def test_strictness_levels(self):
        for strictness in ["gentle", "normal", "hard"]:
            messages = build_interview_prompt(
                theme=None,
                user_goal=None,
                user_concerns=None,
                strictness=strictness,
                character_name="面接官",
                conversation_history=[],
            )
            assert len(messages) >= 1


class TestPresentationPrompt:
    def test_build_presentation_prompt_basic(self):
        messages = build_presentation_prompt(
            theme="新製品発表",
            user_goal="聴衆を惹きつけたい",
            user_concerns="時間配分が苦手",
            strictness="normal",
            character_name="聴衆A",
            conversation_history=[],
            is_qa_phase=False,
        )

        assert len(messages) == 1
        assert messages[0].role == "system"
        assert "聴衆A" in messages[0].content
        assert "プレゼン中" in messages[0].content

    def test_build_presentation_prompt_qa_phase(self):
        messages = build_presentation_prompt(
            theme="研究発表",
            user_goal=None,
            user_concerns=None,
            strictness="hard",
            character_name="教授",
            conversation_history=[
                {"role": "user", "content": "以上が私の研究成果です"},
            ],
            is_qa_phase=True,
        )

        assert len(messages) == 2
        assert "質疑応答" in messages[0].content

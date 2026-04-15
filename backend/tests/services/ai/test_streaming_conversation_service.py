import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.ai.streaming_conversation_service import (
    StreamEvent,
    StreamingConversationService,
)
from app.db.models.practice_session import PracticeSession
from app.db.models.session_participant import SessionParticipant
from app.db.models.ai_character import AiCharacter
from app.services.ai.llm.base import LLMStreamChunk


class TestStreamEvent:
    def test_create_event(self):
        event = StreamEvent(event_type="text_chunk", data={"text": "Hello"})
        assert event.event_type == "text_chunk"
        assert event.data == {"text": "Hello"}


class TestStreamingConversationService:
    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        return StreamingConversationService(mock_db)

    @pytest.mark.asyncio
    async def test_process_message_stream_session_not_found(self, service):
        """Test error handling when session not found."""
        service._session_repo.get_by_id = MagicMock(return_value=None)

        events = []
        async for event in service.process_message_stream(
            session_id=999,
            user_message="Hello",
            generate_audio=False,
        ):
            events.append(event)

        assert len(events) == 1
        assert events[0].event_type == "error"
        assert "not found" in events[0].data["message"]

    @pytest.mark.asyncio
    async def test_process_message_stream_session_not_active(self, service):
        """Test error handling when session is not active."""
        mock_session = MagicMock(status="completed")
        service._session_repo.get_by_id = MagicMock(return_value=mock_session)

        events = []
        async for event in service.process_message_stream(
            session_id=1,
            user_message="Hello",
            generate_audio=False,
        ):
            events.append(event)

        assert len(events) == 1
        assert events[0].event_type == "error"
        assert "not active" in events[0].data["message"]

    @pytest.mark.asyncio
    async def test_stream_text_only(self, service):
        """Test streaming text without audio."""
        mock_session = MagicMock(
            id=1,
            mode="interview",
            theme="技術面接",
            user_goal=None,
            user_concerns=None,
        )

        # Mock LLM stream
        async def mock_stream(*args, **kwargs):
            yield LLMStreamChunk(content="こんにちは。", finish_reason=None)
            yield LLMStreamChunk(content="質問です。", finish_reason=None)
            yield LLMStreamChunk(content="", finish_reason="stop")

        service._llm.generate_stream = mock_stream

        events = []
        async for event in service._stream_text_only(
            session=mock_session,
            conversation_history=[],
            speaker=None,
        ):
            events.append(event)

        assert len(events) == 2  # Only text chunks (finish chunk has no content)
        assert all(e.event_type == "text_chunk" for e in events)
        assert events[0].data["text"] == "こんにちは。"
        assert events[1].data["text"] == "質問です。"

    @pytest.mark.asyncio
    async def test_extract_sentences(self, service):
        """Test sentence extraction logic."""
        # Complete sentences
        sentences = service._extract_sentences("こんにちは。今日はいい天気ですね。")
        assert sentences == ["こんにちは。", "今日はいい天気ですね。"]

        # Incomplete sentence
        sentences = service._extract_sentences("こんにちは。今日は")
        assert sentences == ["こんにちは。", "今日は"]

        # Multiple punctuation types
        sentences = service._extract_sentences("本当ですか？素晴らしい！")
        assert sentences == ["本当ですか？", "素晴らしい！"]

    def test_build_conversation_history(self, service):
        """Test building conversation history from messages."""
        from app.db.models.session_message import SessionMessage

        messages = [
            SessionMessage(
                id=1,
                session_id=1,
                participant_id=None,
                sequence_no=1,
                content="Hello",
            ),
            SessionMessage(
                id=2,
                session_id=1,
                participant_id=1,
                sequence_no=2,
                content="Hi there",
            ),
        ]

        history = service._build_conversation_history(messages)
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there"}

    def test_get_speaker_id(self, service):
        """Test getting VOICEVOX speaker ID."""
        # With character
        character = AiCharacter(
            id=1,
            code="test",
            name="Test Character",
            role="interviewer",
            voice_style="ずんだもん",
            strictness="normal",
        )
        participant = SessionParticipant(
            id=1,
            session_id=1,
            ai_character_id=1,
            display_name="テスター",
        )
        participant.ai_character = character

        speaker_id = service._get_speaker_id(participant)
        assert speaker_id == 3  # ずんだもん

        # Without character
        speaker_id = service._get_speaker_id(None)
        assert speaker_id == 3  # Default ずんだもん

    def test_pick_random_participant(self, service):
        """Test picking random participant."""
        participants = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3),
        ]

        # Should return one of the participants
        picked = service._pick_random_participant(participants)
        assert picked in participants

        # Empty list should return None
        picked = service._pick_random_participant([])
        assert picked is None

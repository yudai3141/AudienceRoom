import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.ai.llm.base import LLMMessage, LLMStreamChunk
from app.services.ai.llm.gemini import GeminiProvider
from app.services.ai.llm.openai import OpenAIProvider


class TestLLMStreamChunk:
    def test_create_chunk(self):
        chunk = LLMStreamChunk(content="Hello", finish_reason=None)
        assert chunk.content == "Hello"
        assert chunk.finish_reason is None

    def test_create_chunk_with_finish_reason(self):
        chunk = LLMStreamChunk(content="", finish_reason="stop")
        assert chunk.content == ""
        assert chunk.finish_reason == "stop"


class TestGeminiProviderStreaming:
    @pytest.mark.asyncio
    async def test_generate_stream_basic(self, monkeypatch):
        """Test basic streaming functionality with mock."""
        provider = GeminiProvider(api_key="test-key", model="gemini-2.0-flash")

        # Mock the chat.send_message_async to return a stream
        mock_chunks = [
            MagicMock(text="Hello"),
            MagicMock(text=" world"),
            MagicMock(text="!"),
        ]

        async def mock_stream():
            for chunk in mock_chunks:
                yield chunk

        mock_chat = MagicMock()
        mock_chat.send_message_async = AsyncMock(return_value=mock_stream())

        mock_model = MagicMock()
        mock_model.start_chat = MagicMock(return_value=mock_chat)

        monkeypatch.setattr(provider, "model", mock_model)

        messages = [LLMMessage(role="user", content="Hi")]
        chunks = []

        async for chunk in provider.generate_stream(messages):
            chunks.append(chunk)

        assert len(chunks) == 4  # 3 text chunks + 1 finish chunk
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"
        assert chunks[2].content == "!"
        assert chunks[3].finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_generate_stream_empty_messages(self):
        """Test that empty message list raises error."""
        provider = GeminiProvider(api_key="test-key")

        with pytest.raises(ValueError, match="At least one user message is required"):
            async for _ in provider.generate_stream([]):
                pass


class TestOpenAIProviderStreaming:
    @pytest.mark.asyncio
    async def test_generate_stream_basic(self, monkeypatch):
        """Test basic streaming functionality with mock."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")

        # Mock stream response
        class MockChoice:
            def __init__(self, delta_content, finish_reason=None):
                self.delta = MagicMock(content=delta_content)
                self.finish_reason = finish_reason

        class MockChunk:
            def __init__(self, choices):
                self.choices = choices

        mock_stream = [
            MockChunk([MockChoice("Hello")]),
            MockChunk([MockChoice(" world")]),
            MockChunk([MockChoice("!")]),
            MockChunk([MockChoice(None, finish_reason="stop")]),
        ]

        async def mock_create(*args, **kwargs):
            for chunk in mock_stream:
                yield chunk

        mock_client = MagicMock()
        mock_client.chat.completions.create = mock_create
        monkeypatch.setattr(provider, "client", mock_client)

        messages = [LLMMessage(role="user", content="Hi")]
        chunks = []

        async for chunk in provider.generate_stream(messages):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert chunks[0].content == "Hello"
        assert chunks[1].content == " world"
        assert chunks[2].content == "!"
        assert chunks[3].finish_reason == "stop"


class TestSentenceExtraction:
    """Test sentence extraction logic (will be in streaming service)."""

    def test_extract_japanese_sentences(self):
        """Test extraction of Japanese sentences."""
        import re

        def extract_sentences(text: str) -> list[str]:
            parts = re.split(r"([。！？!?])", text)
            sentences = []
            for i in range(0, len(parts) - 1, 2):
                if i + 1 < len(parts):
                    sentences.append(parts[i] + parts[i + 1])
                else:
                    sentences.append(parts[i])
            if len(parts) % 2 == 1 and parts[-1]:
                sentences.append(parts[-1])
            return sentences

        # Test complete sentences
        text = "こんにちは。今日はいい天気ですね。"
        sentences = extract_sentences(text)
        assert sentences == ["こんにちは。", "今日はいい天気ですね。"]

        # Test with incomplete sentence
        text = "こんにちは。今日は"
        sentences = extract_sentences(text)
        assert sentences == ["こんにちは。", "今日は"]

        # Test with question and exclamation
        text = "本当ですか？素晴らしい！"
        sentences = extract_sentences(text)
        assert sentences == ["本当ですか？", "素晴らしい！"]

        # Test with English period (not split by our regex)
        text = "Hello。これはテストです。"
        sentences = extract_sentences(text)
        assert sentences == ["Hello。", "これはテストです。"]

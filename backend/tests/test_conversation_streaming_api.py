import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.ai.streaming_conversation_service import StreamEvent


@pytest.fixture(autouse=True)
def mock_llm_provider():
    """Mock LLM provider to avoid requiring API keys in tests."""
    with patch("app.services.ai.llm.get_llm_provider") as mock:
        mock_provider = MagicMock()
        mock.return_value = mock_provider
        yield mock_provider


class TestConversationStreamingAPI:
    """Test streaming conversation API endpoints."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_send_message_stream_endpoint_exists(self, client):
        """Test that streaming endpoint exists."""
        # This will fail with 401 or 400, but not 404
        response = client.post(
            "/conversation/message/stream",
            json={"session_id": 1, "message": "Hello", "generate_audio": False},
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_start_conversation_stream_endpoint_exists(self, client):
        """Test that start streaming endpoint exists."""
        response = client.post(
            "/conversation/start/stream",
            json={"session_id": 1, "generate_audio": False},
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    def test_stream_event_format(self):
        """Test SSE event formatting."""
        import json

        event = StreamEvent(event_type="text_chunk", data={"text": "Hello"})

        # Format as SSE
        sse_output = f"event: {event.event_type}\n"
        sse_output += f"data: {json.dumps(event.data, ensure_ascii=False)}\n\n"

        assert "event: text_chunk" in sse_output
        assert "data: " in sse_output
        assert "Hello" in sse_output

    def test_stream_event_types(self):
        """Test different event types."""
        # Metadata event
        event = StreamEvent(
            event_type="metadata",
            data={"participant_id": 1, "speaker_id": 3},
        )
        assert event.event_type == "metadata"
        assert event.data["participant_id"] == 1

        # Text chunk event
        event = StreamEvent(event_type="text_chunk", data={"text": "こんにちは"})
        assert event.event_type == "text_chunk"
        assert event.data["text"] == "こんにちは"

        # Audio chunk event
        event = StreamEvent(
            event_type="audio_chunk",
            data={"audio_base64": "base64data", "sequence": 1, "text": "こんにちは"},
        )
        assert event.event_type == "audio_chunk"
        assert event.data["sequence"] == 1

        # Complete event
        event = StreamEvent(
            event_type="complete",
            data={"text": "Full response", "audio_sequence_count": 3},
        )
        assert event.event_type == "complete"
        assert event.data["audio_sequence_count"] == 3

        # Error event
        event = StreamEvent(event_type="error", data={"message": "Something went wrong"})
        assert event.event_type == "error"
        assert "wrong" in event.data["message"]

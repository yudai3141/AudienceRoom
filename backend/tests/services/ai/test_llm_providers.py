import pytest

from app.services.ai.llm.base import LLMMessage, LLMResponse


class TestLLMMessage:
    def test_create_user_message(self):
        msg = LLMMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_create_system_message(self):
        msg = LLMMessage(role="system", content="You are a helpful assistant")
        assert msg.role == "system"
        assert msg.content == "You are a helpful assistant"

    def test_create_assistant_message(self):
        msg = LLMMessage(role="assistant", content="Hi there!")
        assert msg.role == "assistant"
        assert msg.content == "Hi there!"


class TestLLMResponse:
    def test_create_response(self):
        response = LLMResponse(
            content="Hello, how can I help?",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert response.content == "Hello, how can I help?"
        assert response.model == "test-model"
        assert response.usage["total_tokens"] == 15

    def test_create_response_without_usage(self):
        response = LLMResponse(
            content="Hello",
            model="test-model",
        )
        assert response.content == "Hello"
        assert response.usage is None

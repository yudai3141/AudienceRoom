import json
import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .base import LLMMessage, LLMProvider, LLMResponse, LLMStreamChunk

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLMプロバイダー"""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    def _convert_messages(self, messages: list[LLMMessage]) -> list[dict]:
        """LLMMessageリストをOpenAI形式に変換する"""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        openai_messages = self._convert_messages(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage=usage,
        )

    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
    ) -> dict:
        openai_messages = self._convert_messages(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[LLMStreamChunk]:
        """OpenAIからストリーミングレスポンスを生成する"""
        openai_messages = self._convert_messages(messages)

        # stream=True の場合、create() は直接 async generator を返す
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield LLMStreamChunk(
                    content=chunk.choices[0].delta.content, finish_reason=None
                )

            if chunk.choices and chunk.choices[0].finish_reason:
                yield LLMStreamChunk(
                    content="", finish_reason=chunk.choices[0].finish_reason
                )

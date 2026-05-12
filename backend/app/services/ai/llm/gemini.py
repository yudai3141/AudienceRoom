import json
import logging
from collections.abc import AsyncIterator

from google import genai
from google.genai import types

from .base import LLMMessage, LLMProvider, LLMResponse, LLMStreamChunk

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLMプロバイダー (google-genai SDK)"""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        self._client = genai.Client(api_key=api_key)
        self.model_name = model

    def _build_contents(
        self, messages: list[LLMMessage]
    ) -> tuple[str | None, list[types.Content]]:
        """LLMMessageリストを新SDK形式に変換する。

        Returns:
            (system_instruction, contents) のタプル
        """
        system_instruction: str | None = None
        contents: list[types.Content] = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append(
                    types.Content(role="user", parts=[types.Part(text=msg.content)])
                )
            elif msg.role == "assistant":
                contents.append(
                    types.Content(role="model", parts=[types.Part(text=msg.content)])
                )

        return system_instruction, contents

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        system_instruction, contents = self._build_contents(messages)
        if not contents:
            raise ValueError("At least one user message is required")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        usage = None
        if response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }

        return LLMResponse(
            content=response.text or "",
            model=self.model_name,
            usage=usage,
        )

    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
    ) -> dict:
        system_instruction, contents = self._build_contents(messages)
        if not contents:
            raise ValueError("At least one user message is required")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            response_mime_type="application/json",
        )

        response = await self._client.aio.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config,
        )

        try:
            return json.loads(response.text or "")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response.text}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

    async def generate_stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[LLMStreamChunk]:
        system_instruction, contents = self._build_contents(messages)
        if not contents:
            raise ValueError("At least one user message is required")

        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self.model_name,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield LLMStreamChunk(content=chunk.text, finish_reason=None)

        yield LLMStreamChunk(content="", finish_reason="stop")

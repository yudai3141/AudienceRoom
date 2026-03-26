import json
import logging

import google.generativeai as genai

from .base import LLMMessage, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash"):
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)

    def _convert_messages(
        self, messages: list[LLMMessage]
    ) -> tuple[str | None, list[dict]]:
        """Convert LLMMessage list to Gemini format.

        Returns:
            Tuple of (system_instruction, history)
        """
        system_instruction = None
        history = []

        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                history.append({"role": "user", "parts": [msg.content]})
            elif msg.role == "assistant":
                history.append({"role": "model", "parts": [msg.content]})

        return system_instruction, history

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        system_instruction, history = self._convert_messages(messages)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        model = self.model
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
            )

        if len(history) == 0:
            raise ValueError("At least one user message is required")

        last_message = history[-1]
        chat_history = history[:-1] if len(history) > 1 else []

        chat = model.start_chat(history=chat_history)
        response = await chat.send_message_async(
            last_message["parts"][0],
            generation_config=generation_config,
        )

        usage = None
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = {
                "prompt_tokens": response.usage_metadata.prompt_token_count,
                "completion_tokens": response.usage_metadata.candidates_token_count,
                "total_tokens": response.usage_metadata.total_token_count,
            }

        return LLMResponse(
            content=response.text,
            model=self.model_name,
            usage=usage,
        )

    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
    ) -> dict:
        system_instruction, history = self._convert_messages(messages)

        generation_config = genai.GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
        )

        model = self.model
        if system_instruction:
            model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
            )

        if len(history) == 0:
            raise ValueError("At least one user message is required")

        last_message = history[-1]
        chat_history = history[:-1] if len(history) > 1 else []

        chat = model.start_chat(history=chat_history)
        response = await chat.send_message_async(
            last_message["parts"][0],
            generation_config=generation_config,
        )

        try:
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response.text}")
            raise ValueError(f"Invalid JSON response from LLM: {e}") from e

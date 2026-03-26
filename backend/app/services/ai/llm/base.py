from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "user" or "assistant" or "system"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            messages: List of messages in the conversation.
            temperature: Sampling temperature (0.0 - 1.0).
            max_tokens: Maximum number of tokens to generate.

        Returns:
            LLMResponse containing the generated content.
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
    ) -> dict:
        """Generate a JSON response from the LLM.

        Args:
            messages: List of messages in the conversation.
            temperature: Sampling temperature (0.0 - 1.0).

        Returns:
            Parsed JSON response as a dictionary.
        """
        pass

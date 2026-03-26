from functools import lru_cache

from app.core.config import settings

from .base import LLMProvider
from .gemini import GeminiProvider
from .openai import OpenAIProvider


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider.

    Returns:
        LLMProvider instance based on LLM_PROVIDER environment variable.

    Raises:
        ValueError: If the provider is not configured or API key is missing.
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Gemini provider")
        return GeminiProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )

    if provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        return OpenAIProvider(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )

    raise ValueError(f"Unknown LLM provider: {provider}")

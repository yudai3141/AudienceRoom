from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMMessage:
    role: str  # "user" または "assistant" または "system"
    content: str


@dataclass
class LLMResponse:
    content: str
    model: str
    usage: dict | None = None


@dataclass
class LLMStreamChunk:
    """LLMからのストリーミングレスポンスのチャンク"""

    content: str
    finish_reason: str | None = None


class LLMProvider(ABC):
    """LLMプロバイダーの抽象基底クラス"""

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        """LLMからレスポンスを生成する

        Args:
            messages: 会話メッセージのリスト
            temperature: サンプリング温度 (0.0 - 1.0)
            max_tokens: 生成する最大トークン数

        Returns:
            生成されたコンテンツを含むLLMResponse
        """
        pass

    @abstractmethod
    async def generate_json(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
    ) -> dict:
        """LLMからJSONレスポンスを生成する

        Args:
            messages: 会話メッセージのリスト
            temperature: サンプリング温度 (0.0 - 1.0)

        Returns:
            パースされたJSON辞書
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[LLMStreamChunk]:
        """LLMからストリーミングレスポンスを生成する

        Args:
            messages: 会話メッセージのリスト
            temperature: サンプリング温度 (0.0 - 1.0)
            max_tokens: 生成する最大トークン数

        Yields:
            LLMStreamChunk: 利用可能になったテキストチャンク
        """
        pass

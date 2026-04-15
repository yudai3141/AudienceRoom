"""
共通テストフィクスチャ

このファイルに定義されたフィクスチャは全てのテストで利用可能。
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
import app.db.models  # noqa: F401

engine = create_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture()
def db() -> Session:
    """テスト用データベースセッション

    各テスト実行後に自動的にロールバックされる。
    """
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(autouse=True)
def mock_llm_provider():
    """LLM プロバイダーをモックして API キー不要にする

    このフィクスチャは全テストに自動適用される (autouse=True)。
    StreamingConversationService や ConversationService が使用する
    get_llm_provider() をモックする。

    重要:
        patch() は「使用される場所」でパッチを当てる必要がある。
        例: StreamingConversationService 内で使う場合
        → "app.services.ai.streaming_conversation_service.get_llm_provider"

    Yields:
        MagicMock: モックされた LLM プロバイダーインスタンス
    """
    # 複数の使用場所でパッチを当てる
    with patch(
        "app.services.ai.streaming_conversation_service.get_llm_provider"
    ) as mock_streaming, patch(
        "app.services.ai.conversation_service.get_llm_provider"
    ) as mock_conversation:
        mock_provider = MagicMock()
        mock_streaming.return_value = mock_provider
        mock_conversation.return_value = mock_provider
        yield mock_provider

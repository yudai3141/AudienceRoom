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


def _guard_test_database() -> None:
    """テストを「テスト専用 DB」以外に向けて実行することを拒否する。

    目的:
    - dev DB (アプリと共有) を汚染しない。一部テストはグローバル状態に依存するため、
      コミット済みの seed/デモデータがあると壊れる。
    - 本番 DB に対してテストを走らせる事故を防ぐ。

    許可条件: APP_ENV=test、または DATABASE_URL の DB 名が `_test` で終わる。
    正しい実行方法は README『12.6 テスト / DB データ衛生』および `make test-backend`。
    """
    url = settings.DATABASE_URL
    db_name = url.rsplit("/", 1)[-1].split("?")[0]
    if not settings.is_testing and not db_name.endswith("_test"):
        raise RuntimeError(
            f"Refusing to run tests against non-test database '{db_name}'. "
            "テストは専用のテスト DB に対してのみ実行できます。"
            "`make test-backend` を使うか、APP_ENV=test と DATABASE_URL を "
            "`*_test` DB に設定してください (README 12.6 参照)。"
        )


_guard_test_database()

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

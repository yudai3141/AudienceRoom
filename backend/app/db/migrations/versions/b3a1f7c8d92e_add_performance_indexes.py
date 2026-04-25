"""add performance indexes

Revision ID: b3a1f7c8d92e
Revises: af1d032b65fb
Create Date: 2026-04-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b3a1f7c8d92e'
down_revision: Union[str, Sequence[str], None] = 'af1d032b65fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add indexes for query performance."""
    # session_messages: メッセージ一覧取得 (WHERE session_id=? ORDER BY sequence_no)
    op.create_index(
        "ix_session_messages_session_seq",
        "session_messages",
        ["session_id", "sequence_no"],
    )

    # session_feedback: セッションごとのフィードバック検索 (WHERE session_id=?)
    op.create_index(
        "ix_session_feedback_session_id",
        "session_feedback",
        ["session_id"],
    )

    # feedback_metrics: フィードバックごとのメトリクス一覧 (WHERE feedback_id=?)
    op.create_index(
        "ix_feedback_metrics_feedback_id",
        "feedback_metrics",
        ["feedback_id"],
    )

    # session_participants: セッションごとの参加者一覧 (WHERE session_id=? ORDER BY seat_index)
    op.create_index(
        "ix_session_participants_session_seat",
        "session_participants",
        ["session_id", "seat_index"],
    )

    # practice_sessions: ユーザのセッション検索 (WHERE user_id=? AND deleted_at IS NULL)
    op.create_index(
        "ix_practice_sessions_user_deleted",
        "practice_sessions",
        ["user_id", "deleted_at"],
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index("ix_practice_sessions_user_deleted", table_name="practice_sessions")
    op.drop_index("ix_session_participants_session_seat", table_name="session_participants")
    op.drop_index("ix_feedback_metrics_feedback_id", table_name="feedback_metrics")
    op.drop_index("ix_session_feedback_session_id", table_name="session_feedback")
    op.drop_index("ix_session_messages_session_seq", table_name="session_messages")

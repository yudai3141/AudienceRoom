"""create topic memory tables (Plan B)

topics / topic_nodes / topic_edges を新設し、practice_sessions に topic_id を追加する。
詳細は backend/docs/db-schema-plan-b-topics.md。

Revision ID: c1d2e3f4a5b6
Revises: b3a1f7c8d92e
Create Date: 2026-06-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4a5b6'
down_revision: Union[str, Sequence[str], None] = 'b3a1f7c8d92e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create topic memory layer tables and link practice_sessions."""
    # topics: 面接で話すエピソードを育てる永続単位
    op.create_table(
        'topics',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.BigInteger(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
        sa.Column('completeness_score', sa.Integer(), nullable=True),
        sa.Column('current_summary', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'archived')", name='ck_topics_status'),
        sa.CheckConstraint('completeness_score >= 0 AND completeness_score <= 100', name='ck_topics_completeness_score'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    # ユーザの有効トピック一覧 (WHERE user_id=? AND deleted_at IS NULL)
    op.create_index(
        'ix_topics_user_deleted',
        'topics',
        ['user_id'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )

    # topic_nodes: トピック内の論点・要素 (グラフのノード)
    op.create_table(
        'topic_nodes',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=True),
        sa.Column('label', sa.String(length=160), nullable=False),
        sa.Column('detail', sa.Text(), nullable=True),
        sa.Column('coverage', sa.String(length=20), server_default='gap', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint("coverage IN ('covered', 'weak', 'gap')", name='ck_topic_nodes_coverage'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    # トピック詳細のツリー/グラフ描画 (WHERE topic_id=? ORDER BY sort_order)
    op.create_index('ix_topic_nodes_topic', 'topic_nodes', ['topic_id', 'sort_order'])
    # 質問生成でのノード候補抽出・弱点数集計 (WHERE topic_id=? AND coverage IN ...)
    op.create_index('ix_topic_nodes_topic_coverage', 'topic_nodes', ['topic_id', 'coverage'])

    # topic_edges: ノード間の関係 (グラフのエッジ, contradicts を含む)
    op.create_table(
        'topic_edges',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('topic_id', sa.BigInteger(), nullable=False),
        sa.Column('source_node_id', sa.BigInteger(), nullable=False),
        sa.Column('target_node_id', sa.BigInteger(), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ),
        sa.ForeignKeyConstraint(['source_node_id'], ['topic_nodes.id'], ),
        sa.ForeignKeyConstraint(['target_node_id'], ['topic_nodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('source_node_id', 'target_node_id', 'relation_type', name='uq_topic_edges_src_tgt_rel'),
    )
    # トピックのエッジ取得 (WHERE topic_id=?)
    op.create_index('ix_topic_edges_topic', 'topic_edges', ['topic_id'])

    # practice_sessions に練習対象トピックを追加 (nullable)
    op.add_column('practice_sessions', sa.Column('topic_id', sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        'fk_practice_sessions_topic_id',
        'practice_sessions',
        'topics',
        ['topic_id'],
        ['id'],
    )
    # トピック → 練習回数/最終練習日の集計 (WHERE topic_id=?)
    op.create_index('ix_practice_sessions_topic', 'practice_sessions', ['topic_id'])


def downgrade() -> None:
    """Drop topic memory layer tables and the practice_sessions link."""
    op.drop_index('ix_practice_sessions_topic', table_name='practice_sessions')
    op.drop_constraint('fk_practice_sessions_topic_id', 'practice_sessions', type_='foreignkey')
    op.drop_column('practice_sessions', 'topic_id')

    op.drop_index('ix_topic_edges_topic', table_name='topic_edges')
    op.drop_table('topic_edges')

    op.drop_index('ix_topic_nodes_topic_coverage', table_name='topic_nodes')
    op.drop_index('ix_topic_nodes_topic', table_name='topic_nodes')
    op.drop_table('topic_nodes')

    op.drop_index('ix_topics_user_deleted', table_name='topics')
    op.drop_table('topics')

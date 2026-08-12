"""add issues, symbol_edges, runs tables and repositories.symbol_graph_built_at

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-12 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: str | None = 'a1b2c3d4e5f6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'repositories', sa.Column('symbol_graph_built_at', sa.DateTime(), nullable=True)
    )

    op.create_table(
        'issues',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('repository_id', sa.Uuid(), nullable=False),
        sa.Column('github_issue_id', sa.BigInteger(), nullable=False),
        sa.Column('number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=1024), nullable=False),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('author', sa.String(length=255), nullable=True),
        sa.Column('labels', postgresql.JSONB(), nullable=False),
        sa.Column('state', sa.String(length=20), nullable=False),
        sa.Column('html_url', sa.String(length=2048), nullable=False),
        sa.Column('github_created_at', sa.DateTime(), nullable=True),
        sa.Column('github_updated_at', sa.DateTime(), nullable=True),
        sa.Column('github_closed_at', sa.DateTime(), nullable=True),
        sa.Column('synced_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_id', 'github_issue_id', name='uq_issue_repo_github_id'),
    )
    op.create_index(op.f('ix_issues_repository_id'), 'issues', ['repository_id'], unique=False)

    op.create_table(
        'symbol_edges',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('repository_id', sa.Uuid(), nullable=False),
        sa.Column('from_chunk_id', sa.Uuid(), nullable=False),
        sa.Column('to_chunk_id', sa.Uuid(), nullable=False),
        sa.Column('edge_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['from_chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_chunk_id'], ['chunks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_symbol_edges_repo_from', 'symbol_edges', ['repository_id', 'from_chunk_id']
    )
    op.create_index('ix_symbol_edges_repo_to', 'symbol_edges', ['repository_id', 'to_chunk_id'])

    op.create_table(
        'runs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('repository_id', sa.Uuid(), nullable=False),
        sa.Column('issue_id', sa.Uuid(), nullable=True),
        sa.Column('run_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('langgraph_thread_id', sa.String(length=64), nullable=False),
        sa.Column('implementation_plan', postgresql.JSONB(), nullable=True),
        sa.Column('validation_errors', postgresql.JSONB(), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issue_id'], ['issues.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_runs_repository_id'), 'runs', ['repository_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_runs_repository_id'), table_name='runs')
    op.drop_table('runs')
    op.drop_index('ix_symbol_edges_repo_to', table_name='symbol_edges')
    op.drop_index('ix_symbol_edges_repo_from', table_name='symbol_edges')
    op.drop_table('symbol_edges')
    op.drop_index(op.f('ix_issues_repository_id'), table_name='issues')
    op.drop_table('issues')
    op.drop_column('repositories', 'symbol_graph_built_at')

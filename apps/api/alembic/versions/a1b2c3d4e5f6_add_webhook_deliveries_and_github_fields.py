"""add webhook_deliveries and github/index-status fields to repositories

Revision ID: a1b2c3d4e5f6
Revises: 2308ec89d829
Create Date: 2026-08-11 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = '2308ec89d829'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('repositories', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.add_column('repositories', sa.Column('github_repo_id', sa.BigInteger(), nullable=True))
    op.add_column('repositories', sa.Column('installation_id', sa.BigInteger(), nullable=True))
    op.add_column('repositories', sa.Column('index_started_at', sa.DateTime(), nullable=True))
    op.add_column('repositories', sa.Column('index_completed_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_repositories_full_name'), 'repositories', ['full_name'], unique=False)
    op.create_unique_constraint('uq_repositories_github_repo_id', 'repositories', ['github_repo_id'])

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('github_delivery_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('received_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('github_delivery_id', name='uq_webhook_delivery_github_delivery_id'),
    )


def downgrade() -> None:
    op.drop_table('webhook_deliveries')
    op.drop_constraint('uq_repositories_github_repo_id', 'repositories', type_='unique')
    op.drop_index(op.f('ix_repositories_full_name'), table_name='repositories')
    op.drop_column('repositories', 'index_completed_at')
    op.drop_column('repositories', 'index_started_at')
    op.drop_column('repositories', 'installation_id')
    op.drop_column('repositories', 'github_repo_id')
    op.drop_column('repositories', 'full_name')

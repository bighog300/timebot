"""add usage events table

Revision ID: 20260502_0019
Revises: 20260502_0018
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260502_0019'
down_revision = '20260502_0018'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'usage_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.BigInteger(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    for name, cols in {
        'ix_usage_events_user_id': ['user_id'],
        'ix_usage_events_metric': ['metric'],
        'ix_usage_events_created_at': ['created_at'],
    }.items():
        op.create_index(name, 'usage_events', cols, unique=False)


def downgrade() -> None:
    op.drop_table('usage_events')

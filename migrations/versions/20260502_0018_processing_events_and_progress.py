"""add processing events table

Revision ID: 20260502_0018
Revises: 20260501_0017
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260502_0018'
down_revision = '20260501_0017'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'document_processing_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('stage', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('ai_call_count', sa.Integer(), nullable=True),
        sa.Column('parse_retry_used', sa.String(length=10), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=True),
        sa.Column('safe_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    for name, cols in {
        'ix_document_processing_events_document_id': ['document_id'],
        'ix_document_processing_events_user_id': ['user_id'],
        'ix_document_processing_events_stage': ['stage'],
        'ix_document_processing_events_event_type': ['event_type'],
        'ix_document_processing_events_status': ['status'],
        'ix_document_processing_events_severity': ['severity'],
        'ix_document_processing_events_created_at': ['created_at'],
    }.items():
        op.create_index(name, 'document_processing_events', cols, unique=False)


def downgrade() -> None:
    op.drop_table('document_processing_events')

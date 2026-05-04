"""divorce communications phase6

Revision ID: 20260504_0044
Revises: 20260504_0043
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0044'
down_revision = '20260504_0043'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'divorce_communications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_email_id', sa.String(length=255), nullable=True),
        sa.Column('source_message_id', sa.String(length=255), nullable=True),
        sa.Column('sender', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('recipient', sa.Text(), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=True),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('communication_type', sa.String(length=20), nullable=False, server_default='email'),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='unknown'),
        sa.Column('tone', sa.String(length=30), nullable=False, server_default='unclear'),
        sa.Column('extracted_issues_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('extracted_deadlines_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('extracted_offers_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('extracted_allegations_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('review_status', sa.String(length=20), nullable=False, server_default='suggested'),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_divorce_communications_workspace_id', 'divorce_communications', ['workspace_id'])


def downgrade() -> None:
    op.drop_index('ix_divorce_communications_workspace_id', table_name='divorce_communications')
    op.drop_table('divorce_communications')

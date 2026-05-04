"""divorce vertical foundation

Revision ID: 20260504_0041
Revises: 20260504_0040_prompt_template_advisor_wiring
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0041'
down_revision = '20260504_0040'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('workspaces', sa.Column('workspace_type', sa.String(length=32), nullable=False, server_default='general'))
    op.add_column('workspaces', sa.Column('matter_title', sa.String(length=255), nullable=True))
    op.add_column('workspaces', sa.Column('jurisdiction', sa.String(length=255), nullable=True))
    op.add_column('workspaces', sa.Column('spouse_or_other_party_name', sa.String(length=255), nullable=True))
    op.add_column('workspaces', sa.Column('key_dates_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_table('divorce_timeline_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_date', sa.Date(), nullable=True),
        sa.Column('precision', sa.String(length=20), nullable=False, server_default='inferred'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='admin'),
        sa.Column('source_document_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('documents.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_quote', sa.Text(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('reviewed_status', sa.String(length=20), nullable=False, server_default='suggested'),
        sa.Column('include_in_report', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table('divorce_reports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('report_type', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('evidence_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
    )

def downgrade() -> None:
    op.drop_table('divorce_reports')
    op.drop_table('divorce_timeline_items')
    op.drop_column('workspaces', 'key_dates_json')
    op.drop_column('workspaces', 'spouse_or_other_party_name')
    op.drop_column('workspaces', 'jurisdiction')
    op.drop_column('workspaces', 'matter_title')
    op.drop_column('workspaces', 'workspace_type')

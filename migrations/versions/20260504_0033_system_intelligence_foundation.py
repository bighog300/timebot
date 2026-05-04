"""system intelligence foundation

Revision ID: 20260504_0033
Revises: 20260504_0032
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0033'
down_revision = '20260504_0032'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_intelligence_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=120), nullable=True),
        sa.Column('jurisdiction', sa.String(length=120), nullable=True),
        sa.Column('storage_uri', sa.String(length=1024), nullable=True),
        sa.Column('mime_type', sa.String(length=255), nullable=True),
        sa.Column('content_hash', sa.String(length=128), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('indexed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('system_intelligence_web_references',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False), sa.Column('canonical_url', sa.String(length=2048), nullable=True),
        sa.Column('source_domain', sa.String(length=255), nullable=True), sa.Column('jurisdiction', sa.String(length=120), nullable=True),
        sa.Column('court_or_institution', sa.String(length=255), nullable=True), sa.Column('document_type', sa.String(length=120), nullable=True),
        sa.Column('legal_area', sa.String(length=120), nullable=True), sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('key_points_json', sa.JSON(), nullable=True), sa.Column('citation_text', sa.Text(), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=True), sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content_hash', sa.String(length=128), nullable=True), sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.PrimaryKeyConstraint('id'))
    op.create_table('system_intelligence_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('actor', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False), sa.Column('target_type', sa.String(length=64), nullable=False),
        sa.Column('target_id', sa.String(length=64), nullable=False), sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False), sa.PrimaryKeyConstraint('id'))
    op.create_table('system_intelligence_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True), sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_drive_file_id', sa.String(length=255), nullable=True), sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('suggested_category', sa.String(length=120), nullable=True), sa.Column('suggested_jurisdiction', sa.String(length=120), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True), sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('admin_notes', sa.Text(), nullable=True), sa.Column('reviewed_by_admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resulting_system_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['resulting_system_document_id'], ['system_intelligence_documents.id']),
        sa.ForeignKeyConstraint(['reviewed_by_admin_id'], ['users.id']),
        sa.ForeignKeyConstraint(['source_document_id'], ['documents.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id']),
        sa.PrimaryKeyConstraint('id'))
    op.create_table('system_intelligence_chunks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False), sa.Column('system_document_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('web_reference_id', postgresql.UUID(as_uuid=True), nullable=True), sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False), sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['system_document_id'], ['system_intelligence_documents.id']),
        sa.ForeignKeyConstraint(['web_reference_id'], ['system_intelligence_web_references.id']), sa.PrimaryKeyConstraint('id'))


def downgrade() -> None:
    op.drop_table('system_intelligence_chunks')
    op.drop_table('system_intelligence_submissions')
    op.drop_table('system_intelligence_audit_logs')
    op.drop_table('system_intelligence_web_references')
    op.drop_table('system_intelligence_documents')

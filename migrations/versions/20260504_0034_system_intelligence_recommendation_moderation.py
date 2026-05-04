"""system intelligence recommendation moderation

Revision ID: 20260504_0034
Revises: 20260504_0033
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0034_system_intelligence_recommendation_moderation'
down_revision = '20260504_0033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('system_intelligence_submissions', sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('system_intelligence_documents', sa.Column('source_user_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('system_intelligence_documents', sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('system_intelligence_documents', sa.Column('source_drive_file_id', sa.String(length=255), nullable=True))
    op.create_foreign_key(None, 'system_intelligence_documents', 'users', ['source_user_id'], ['id'])
    op.create_foreign_key(None, 'system_intelligence_documents', 'documents', ['source_document_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'system_intelligence_documents', type_='foreignkey')
    op.drop_constraint(None, 'system_intelligence_documents', type_='foreignkey')
    op.drop_column('system_intelligence_documents', 'source_drive_file_id')
    op.drop_column('system_intelligence_documents', 'source_document_id')
    op.drop_column('system_intelligence_documents', 'source_user_id')
    op.drop_column('system_intelligence_submissions', 'reviewed_at')

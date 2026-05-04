"""system intelligence document processing fields

Revision ID: 20260504_0034
Revises: 20260504_0033
"""
from alembic import op
import sqlalchemy as sa

revision = '20260504_0034'
down_revision = '20260504_0033'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('system_intelligence_documents', sa.Column('original_filename', sa.String(length=500), nullable=True))
    op.add_column('system_intelligence_documents', sa.Column('size_bytes', sa.Integer(), nullable=True))
    op.add_column('system_intelligence_documents', sa.Column('extraction_status', sa.String(length=16), nullable=False, server_default='pending'))
    op.add_column('system_intelligence_documents', sa.Column('extraction_error', sa.Text(), nullable=True))
    op.add_column('system_intelligence_documents', sa.Column('index_status', sa.String(length=16), nullable=False, server_default='pending'))
    op.add_column('system_intelligence_documents', sa.Column('index_error', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('system_intelligence_documents', 'index_error')
    op.drop_column('system_intelligence_documents', 'index_status')
    op.drop_column('system_intelligence_documents', 'extraction_error')
    op.drop_column('system_intelligence_documents', 'extraction_status')
    op.drop_column('system_intelligence_documents', 'size_bytes')
    op.drop_column('system_intelligence_documents', 'original_filename')

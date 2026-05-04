"""divorce tasks phase2

Revision ID: 20260504_0042
Revises: 20260504_0041
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0042'
down_revision = '20260504_0041'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('document_action_items', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('document_action_items', sa.Column('source_document_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('document_action_items', sa.Column('due_date', sa.Date(), nullable=True))
    op.add_column('document_action_items', sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'))
    op.add_column('document_action_items', sa.Column('status', sa.String(length=20), nullable=False, server_default='open'))
    op.add_column('document_action_items', sa.Column('category', sa.String(length=40), nullable=False, server_default='admin'))
    op.add_column('document_action_items', sa.Column('evidence_refs_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('document_action_items', sa.Column('source_quote', sa.Text(), nullable=True))
    op.add_column('document_action_items', sa.Column('source_snippet', sa.Text(), nullable=True))

def downgrade() -> None:
    for col in ['source_snippet','source_quote','evidence_refs_json','category','status','priority','due_date','source_document_id','workspace_id']:
        op.drop_column('document_action_items', col)

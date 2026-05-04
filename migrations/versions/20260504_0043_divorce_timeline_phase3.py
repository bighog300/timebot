"""divorce timeline phase3

Revision ID: 20260504_0043
Revises: 20260504_0042
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260504_0043'
down_revision = '20260504_0042'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column('divorce_timeline_items', 'precision', new_column_name='date_precision', existing_type=sa.String(length=20))
    op.alter_column('divorce_timeline_items', 'reviewed_status', new_column_name='review_status', existing_type=sa.String(length=20))
    op.add_column('divorce_timeline_items', sa.Column('source_snippet', sa.Text(), nullable=True))
    op.add_column('divorce_timeline_items', sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'))

def downgrade() -> None:
    op.drop_column('divorce_timeline_items', 'metadata_json')
    op.drop_column('divorce_timeline_items', 'source_snippet')
    op.alter_column('divorce_timeline_items', 'review_status', new_column_name='reviewed_status', existing_type=sa.String(length=20))
    op.alter_column('divorce_timeline_items', 'date_precision', new_column_name='precision', existing_type=sa.String(length=20))

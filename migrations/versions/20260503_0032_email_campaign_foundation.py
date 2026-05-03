"""email campaign foundation

Revision ID: 20260503_0032
Revises: 20260503_0031
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0032'
down_revision = '20260503_0031'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('audience_type', sa.String(length=64), nullable=False, server_default='all_users'),
        sa.Column('audience_filters_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('subject_override', sa.String(length=500), nullable=True),
        sa.Column('preheader_override', sa.String(length=500), nullable=True),
        sa.Column('variables_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by_admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by_admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['updated_by_admin_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_campaigns_name'), 'email_campaigns', ['name'], unique=False)
    op.create_index(op.f('ix_email_campaigns_status'), 'email_campaigns', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_campaigns_status'), table_name='email_campaigns')
    op.drop_index(op.f('ix_email_campaigns_name'), table_name='email_campaigns')
    op.drop_table('email_campaigns')

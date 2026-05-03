"""email admin foundation

Revision ID: 20260503_0030
Revises: 20260503_0029
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0030'
down_revision = '20260503_0029'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_provider_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('from_email', sa.String(length=255), nullable=False),
        sa.Column('from_name', sa.String(length=255), nullable=True),
        sa.Column('reply_to', sa.String(length=255), nullable=True),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', name='uq_email_provider_configs_provider'),
    )
    op.create_index(op.f('ix_email_provider_configs_provider'), 'email_provider_configs', ['provider'], unique=False)

    op.create_table(
        'email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('preheader', sa.String(length=500), nullable=True),
        sa.Column('html_body', sa.Text(), nullable=False),
        sa.Column('text_body', sa.Text(), nullable=True),
        sa.Column('variables_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_by_admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_by_admin_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug', name='uq_email_templates_slug'),
    )
    op.create_index(op.f('ix_email_templates_slug'), 'email_templates', ['slug'], unique=False)
    op.create_index(op.f('ix_email_templates_category'), 'email_templates', ['category'], unique=False)
    op.create_index(op.f('ix_email_templates_status'), 'email_templates', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_templates_status'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_category'), table_name='email_templates')
    op.drop_index(op.f('ix_email_templates_slug'), table_name='email_templates')
    op.drop_table('email_templates')
    op.drop_index(op.f('ix_email_provider_configs_provider'), table_name='email_provider_configs')
    op.drop_table('email_provider_configs')

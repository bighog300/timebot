"""add email send logs

Revision ID: 20260503_0031
Revises: 20260503_0030
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0031'
down_revision = '20260503_0030'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'email_send_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('recipient_email', sa.String(length=255), nullable=False),
        sa.Column('from_email', sa.String(length=255), nullable=False),
        sa.Column('from_name', sa.String(length=255), nullable=True),
        sa.Column('reply_to', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('error_message_sanitized', sa.Text(), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('failed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_send_logs_provider'), 'email_send_logs', ['provider'], unique=False)
    op.create_index(op.f('ix_email_send_logs_recipient_email'), 'email_send_logs', ['recipient_email'], unique=False)
    op.create_index(op.f('ix_email_send_logs_status'), 'email_send_logs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_send_logs_status'), table_name='email_send_logs')
    op.drop_index(op.f('ix_email_send_logs_recipient_email'), table_name='email_send_logs')
    op.drop_index(op.f('ix_email_send_logs_provider'), table_name='email_send_logs')
    op.drop_table('email_send_logs')

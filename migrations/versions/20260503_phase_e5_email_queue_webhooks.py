"""phase e5 email queue + webhooks

Revision ID: 20260503e5
Revises: 
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503e5'
down_revision = '20260503_0033'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('email_provider_configs', sa.Column('webhook_secret_encrypted', sa.Text(), nullable=True))
    op.add_column('email_campaigns', sa.Column('send_started_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaigns', sa.Column('send_completed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaigns', sa.Column('send_failed_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaigns', sa.Column('send_error_sanitized', sa.Text(), nullable=True))
    op.add_column('email_campaign_recipients', sa.Column('queued_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaign_recipients', sa.Column('delivered_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaign_recipients', sa.Column('bounced_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaign_recipients', sa.Column('complained_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('email_campaign_recipients', sa.Column('provider_event_id', sa.String(length=255), nullable=True))
    op.add_column('email_campaign_recipients', sa.Column('last_event_at', sa.TIMESTAMP(timezone=True), nullable=True))
    op.create_table('email_provider_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('provider_event_id', sa.String(length=255), nullable=True),
        sa.Column('provider_message_id', sa.String(length=255), nullable=True),
        sa.Column('recipient_email', sa.String(length=255), nullable=True),
        sa.Column('campaign_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('send_log_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('payload_json_sanitized', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['send_log_id'], ['email_send_logs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider', 'provider_event_id', name='uq_email_provider_event_provider_event_id')
    )

def downgrade():
    op.drop_table('email_provider_events')

"""prompt system hardening

Revision ID: 20260503_0029
Revises: 20260503_0025
"""
from alembic import op
import sqlalchemy as sa

revision = '20260503_0029'
down_revision = '20260503_0028'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    WITH ranked AS (
      SELECT id, type, ROW_NUMBER() OVER (PARTITION BY type ORDER BY COALESCE(updated_at, created_at) DESC, created_at DESC) AS rn
      FROM prompt_templates WHERE is_default = true
    )
    UPDATE prompt_templates p
    SET is_default = false
    FROM ranked r
    WHERE p.id = r.id AND r.rn > 1
    """)
    op.create_index('uq_prompt_templates_one_default_per_type', 'prompt_templates', ['type'], unique=True, postgresql_where=sa.text('is_default = true'))
    op.add_column('prompt_templates', sa.Column('fallback_order', sa.String(length=32), nullable=False, server_default='provider_then_model'))
    op.add_column('prompt_templates', sa.Column('max_fallback_attempts', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('prompt_templates', sa.Column('retry_on_provider_errors', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('prompt_templates', sa.Column('retry_on_rate_limit', sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column('prompt_templates', sa.Column('retry_on_validation_error', sa.Boolean(), nullable=False, server_default=sa.false()))

    op.add_column('prompt_execution_logs', sa.Column('fallback_reason', sa.String(length=64), nullable=True))
    op.add_column('prompt_execution_logs', sa.Column('primary_provider', sa.String(length=32), nullable=True))
    op.add_column('prompt_execution_logs', sa.Column('primary_model', sa.String(length=120), nullable=True))

    op.add_column('chatbot_settings', sa.Column('prompt_daily_cost_threshold_usd', sa.Float(), nullable=True))
    op.add_column('chatbot_settings', sa.Column('prompt_monthly_cost_threshold_usd', sa.Float(), nullable=True))
    op.add_column('chatbot_settings', sa.Column('prompt_user_cost_threshold_usd', sa.Float(), nullable=True))
    op.add_column('chatbot_settings', sa.Column('prompt_workspace_cost_threshold_usd', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('chatbot_settings', 'prompt_workspace_cost_threshold_usd')
    op.drop_column('chatbot_settings', 'prompt_user_cost_threshold_usd')
    op.drop_column('chatbot_settings', 'prompt_monthly_cost_threshold_usd')
    op.drop_column('chatbot_settings', 'prompt_daily_cost_threshold_usd')
    op.drop_column('prompt_execution_logs', 'primary_model')
    op.drop_column('prompt_execution_logs', 'primary_provider')
    op.drop_column('prompt_execution_logs', 'fallback_reason')
    op.drop_column('prompt_templates', 'retry_on_validation_error')
    op.drop_column('prompt_templates', 'retry_on_rate_limit')
    op.drop_column('prompt_templates', 'retry_on_provider_errors')
    op.drop_column('prompt_templates', 'max_fallback_attempts')
    op.drop_column('prompt_templates', 'fallback_order')
    op.drop_index('uq_prompt_templates_one_default_per_type', table_name='prompt_templates')

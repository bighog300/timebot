"""prompt execution logs

Revision ID: 20260503_0024
Revises: 20260503_0023
Create Date: 2026-05-03 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0024'
down_revision = '20260503_0023'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'prompt_execution_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('prompt_template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('purpose', sa.String(length=64), nullable=True),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider', sa.String(length=32), nullable=False),
        sa.Column('model', sa.String(length=120), nullable=False),
        sa.Column('fallback_used', sa.Boolean(), nullable=False),
        sa.Column('primary_error', sa.Text(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('input_tokens', sa.Integer(), nullable=True),
        sa.Column('output_tokens', sa.Integer(), nullable=True),
        sa.Column('total_tokens', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('source', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    for col in ['prompt_template_id','purpose','actor_user_id','provider','model','fallback_used','success','source','created_at']:
        op.create_index(op.f(f'ix_prompt_execution_logs_{col}'), 'prompt_execution_logs', [col], unique=False)


def downgrade() -> None:
    for col in ['created_at','source','success','fallback_used','model','provider','actor_user_id','purpose','prompt_template_id']:
        op.drop_index(op.f(f'ix_prompt_execution_logs_{col}'), table_name='prompt_execution_logs')
    op.drop_table('prompt_execution_logs')

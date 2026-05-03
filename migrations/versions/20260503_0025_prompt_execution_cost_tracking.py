"""add cost fields to prompt execution logs

Revision ID: 20260503_0025
Revises: 20260503_0024
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa


revision = "20260503_0025"
down_revision = "20260503_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prompt_execution_logs", sa.Column("estimated_cost_usd", sa.Numeric(precision=12, scale=6), nullable=True))
    op.add_column("prompt_execution_logs", sa.Column("currency", sa.String(length=8), nullable=True))
    op.add_column("prompt_execution_logs", sa.Column("pricing_known", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.create_index(op.f("ix_prompt_execution_logs_pricing_known"), "prompt_execution_logs", ["pricing_known"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_prompt_execution_logs_pricing_known"), table_name="prompt_execution_logs")
    op.drop_column("prompt_execution_logs", "pricing_known")
    op.drop_column("prompt_execution_logs", "currency")
    op.drop_column("prompt_execution_logs", "estimated_cost_usd")

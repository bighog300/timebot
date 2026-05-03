"""add provider/model controls to prompt templates

Revision ID: 20260503_0022
Revises: 20260502_0021_add_subscription_admin_fields
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260503_0022"
down_revision = "20260502_0021_add_subscription_admin_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prompt_templates", sa.Column("provider", sa.String(length=32), nullable=False, server_default="openai"))
    op.add_column("prompt_templates", sa.Column("model", sa.String(length=120), nullable=False, server_default="gpt-4o-mini"))
    op.add_column("prompt_templates", sa.Column("temperature", sa.Float(), nullable=False, server_default="0.2"))
    op.add_column("prompt_templates", sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="800"))
    op.add_column("prompt_templates", sa.Column("top_p", sa.Float(), nullable=False, server_default="1.0"))
    op.add_column("prompt_templates", sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("prompt_templates", sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    op.drop_column("prompt_templates", "is_default")
    op.drop_column("prompt_templates", "enabled")
    op.drop_column("prompt_templates", "top_p")
    op.drop_column("prompt_templates", "max_tokens")
    op.drop_column("prompt_templates", "temperature")
    op.drop_column("prompt_templates", "model")
    op.drop_column("prompt_templates", "provider")

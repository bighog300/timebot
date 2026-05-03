"""add fallback provider/model fields to prompt templates

Revision ID: 20260503_0023
Revises: 20260503_0022
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260503_0023"
down_revision = "20260503_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("prompt_templates", sa.Column("fallback_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("prompt_templates", sa.Column("fallback_provider", sa.String(length=32), nullable=True))
    op.add_column("prompt_templates", sa.Column("fallback_model", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("prompt_templates", "fallback_model")
    op.drop_column("prompt_templates", "fallback_provider")
    op.drop_column("prompt_templates", "fallback_enabled")

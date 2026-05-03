"""add subscription admin fields

Revision ID: 20260502_0021_add_subscription_admin_fields
Revises: 20260502_0020
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260502_0021_add_subscription_admin_fields"
down_revision = "20260502_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriptions",
        sa.Column("usage_credits_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "subscriptions",
        sa.Column("limit_overrides_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("subscriptions", "limit_overrides_json")
    op.drop_column("subscriptions", "usage_credits_json")

"""add billing integration fields

Revision ID: 20260504_0036
Revises: 20260504_0035_google_auth_identity
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = '20260504_0036'
down_revision = '20260504_0035_google_auth_identity'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('subscriptions', sa.Column('billing_customer_id', sa.String(length=255), nullable=True))
    op.add_column('subscriptions', sa.Column('billing_subscription_id', sa.String(length=255), nullable=True))
    op.add_column('subscriptions', sa.Column('billing_price_id', sa.String(length=255), nullable=True))
    op.add_column('subscriptions', sa.Column('billing_provider', sa.String(length=50), nullable=True))
    op.add_column('subscriptions', sa.Column('billing_current_period_end', sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('subscriptions', 'billing_current_period_end')
    op.drop_column('subscriptions', 'billing_provider')
    op.drop_column('subscriptions', 'billing_price_id')
    op.drop_column('subscriptions', 'billing_subscription_id')
    op.drop_column('subscriptions', 'billing_customer_id')

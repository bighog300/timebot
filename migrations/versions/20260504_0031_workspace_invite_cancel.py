"""workspace invite canceled_at

Revision ID: 20260504_0031
Revises: 20260503_0027
Create Date: 2026-05-04
"""
from alembic import op
import sqlalchemy as sa

revision = '20260504_0031'
down_revision = '20260503_0027'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('workspace_invites', sa.Column('canceled_at', sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('workspace_invites', 'canceled_at')

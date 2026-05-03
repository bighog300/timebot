"""add user invites

Revision ID: 20260503_0026
Revises: 20260503_0025
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0026'
down_revision = '20260503_0025'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user_invites',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False),
        sa.Column('invited_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('accepted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('canceled_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_invites_email'), 'user_invites', ['email'], unique=False)
    op.create_index(op.f('ix_user_invites_invited_by_user_id'), 'user_invites', ['invited_by_user_id'], unique=False)
    op.create_index(op.f('ix_user_invites_token_hash'), 'user_invites', ['token_hash'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_invites_token_hash'), table_name='user_invites')
    op.drop_index(op.f('ix_user_invites_invited_by_user_id'), table_name='user_invites')
    op.drop_index(op.f('ix_user_invites_email'), table_name='user_invites')
    op.drop_table('user_invites')

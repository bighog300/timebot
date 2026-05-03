"""notifications and messaging

Revision ID: 20260503_0028
Revises: 20260503_0027
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0028'
down_revision = '20260503_0027'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(length=40), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('link_url', sa.String(length=1024), nullable=True),
        sa.Column('read_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    op.create_table('user_message_threads',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('category', sa.String(length=40), nullable=False),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=40), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_user_message_threads_user_id'), 'user_message_threads', ['user_id'], unique=False)

    op.create_table('user_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sender_type', sa.String(length=20), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['sender_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['thread_id'], ['user_message_threads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_user_messages_thread_id'), 'user_messages', ['thread_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_user_messages_thread_id'), table_name='user_messages')
    op.drop_table('user_messages')
    op.drop_index(op.f('ix_user_message_threads_user_id'), table_name='user_message_threads')
    op.drop_table('user_message_threads')
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_table('notifications')

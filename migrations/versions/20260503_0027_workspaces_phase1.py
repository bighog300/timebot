"""workspaces phase 1

Revision ID: 20260503_0027
Revises: 20260503_0026
Create Date: 2026-05-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260503_0027'
down_revision = '20260503_0026'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('workspaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('owner_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_workspaces_owner_user_id', 'workspaces', ['owner_user_id'])
    op.create_table('workspace_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.UniqueConstraint('workspace_id','user_id',name='uq_workspace_member_workspace_user')
    )
    op.create_index('ix_workspace_members_workspace_id', 'workspace_members', ['workspace_id'])
    op.create_index('ix_workspace_members_user_id', 'workspace_members', ['user_id'])
    op.create_table('workspace_invites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('workspace_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('workspaces.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=False, unique=True),
        sa.Column('invited_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('accepted_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    )
    op.create_index('ix_workspace_invites_workspace_id', 'workspace_invites', ['workspace_id'])
    op.create_index('ix_workspace_invites_email', 'workspace_invites', ['email'])
    op.add_column('documents', sa.Column('workspace_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('fk_documents_workspace_id_workspaces','documents','workspaces',['workspace_id'],['id'],ondelete='CASCADE')
    op.create_index('ix_documents_workspace_id','documents',['workspace_id'])

    op.execute("""
    INSERT INTO workspaces (id, name, type, owner_user_id, created_at, updated_at)
    SELECT gen_random_uuid(),
           COALESCE(NULLIF(TRIM(display_name), ''), SPLIT_PART(email, '@', 1), 'Personal') || '''s Workspace',
           'personal',
           u.id,
           now(),
           now()
    FROM users u
    WHERE NOT EXISTS (
        SELECT 1 FROM workspaces w WHERE w.owner_user_id = u.id AND w.type = 'personal'
    )
    """)
    op.execute("""
    INSERT INTO workspace_members (id, workspace_id, user_id, role, created_at, updated_at)
    SELECT gen_random_uuid(), w.id, w.owner_user_id, 'owner', now(), now()
    FROM workspaces w
    WHERE w.type = 'personal' AND w.owner_user_id IS NOT NULL
      AND NOT EXISTS (
          SELECT 1 FROM workspace_members wm WHERE wm.workspace_id = w.id AND wm.user_id = w.owner_user_id
      )
    """)
    op.execute("""
    UPDATE documents d
    SET workspace_id = w.id
    FROM workspaces w
    WHERE d.workspace_id IS NULL
      AND w.owner_user_id = d.user_id
      AND w.type = 'personal'
    """)
    op.alter_column('documents', 'workspace_id', nullable=False)


def downgrade():
    op.alter_column('documents', 'workspace_id', nullable=True)
    op.drop_index('ix_documents_workspace_id', table_name='documents')
    op.drop_constraint('fk_documents_workspace_id_workspaces','documents',type_='foreignkey')
    op.drop_column('documents','workspace_id')
    op.drop_index('ix_workspace_invites_email', table_name='workspace_invites')
    op.drop_index('ix_workspace_invites_workspace_id', table_name='workspace_invites')
    op.drop_table('workspace_invites')
    op.drop_index('ix_workspace_members_user_id', table_name='workspace_members')
    op.drop_index('ix_workspace_members_workspace_id', table_name='workspace_members')
    op.drop_table('workspace_members')
    op.drop_index('ix_workspaces_owner_user_id', table_name='workspaces')
    op.drop_table('workspaces')

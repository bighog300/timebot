"""add admin audit events table

Revision ID: 20260430_0011
Revises: 20260429_0010
Create Date: 2026-04-30 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260430_0011"
down_revision: Union[str, None] = "20260429_0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Text(), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_audit_events_actor_id"), "admin_audit_events", ["actor_id"], unique=False)
    op.create_index(op.f("ix_admin_audit_events_entity_type"), "admin_audit_events", ["entity_type"], unique=False)
    op.create_index(op.f("ix_admin_audit_events_entity_id"), "admin_audit_events", ["entity_id"], unique=False)
    op.create_index(op.f("ix_admin_audit_events_action"), "admin_audit_events", ["action"], unique=False)
    op.create_index(op.f("ix_admin_audit_events_created_at"), "admin_audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_admin_audit_events_created_at"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_action"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_entity_id"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_entity_type"), table_name="admin_audit_events")
    op.drop_index(op.f("ix_admin_audit_events_actor_id"), table_name="admin_audit_events")
    op.drop_table("admin_audit_events")

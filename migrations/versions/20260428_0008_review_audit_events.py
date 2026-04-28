"""add review audit events table

Revision ID: 20260428_0008
Revises: 20260428_0007
Create Date: 2026-04-28 03:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260428_0008"
down_revision: Union[str, None] = "20260428_0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("before_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("after_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_review_audit_events_document_id"), "review_audit_events", ["document_id"], unique=False)
    op.create_index(op.f("ix_review_audit_events_actor_id"), "review_audit_events", ["actor_id"], unique=False)
    op.create_index(op.f("ix_review_audit_events_event_type"), "review_audit_events", ["event_type"], unique=False)
    op.create_index(op.f("ix_review_audit_events_created_at"), "review_audit_events", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_review_audit_events_created_at"), table_name="review_audit_events")
    op.drop_index(op.f("ix_review_audit_events_event_type"), table_name="review_audit_events")
    op.drop_index(op.f("ix_review_audit_events_actor_id"), table_name="review_audit_events")
    op.drop_index(op.f("ix_review_audit_events_document_id"), table_name="review_audit_events")
    op.drop_table("review_audit_events")

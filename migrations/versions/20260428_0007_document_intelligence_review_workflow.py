"""add document intelligence review workflow tables

Revision ID: 20260428_0007
Revises: 20260428_0006
Create Date: 2026-04-28 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260428_0007"
down_revision: Union[str, None] = "20260428_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_intelligence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_points", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("suggested_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("confidence", sa.String(length=20), nullable=False, server_default="low"),
        sa.Column("suggested_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("entities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=True),
        sa.Column("model_version", sa.String(length=100), nullable=True),
        sa.Column("model_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("category_status", sa.String(length=20), nullable=False, server_default="suggested"),
        sa.Column("generated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("confidence IN ('low', 'medium', 'high')", name="valid_intelligence_confidence"),
        sa.CheckConstraint(
            "category_status IN ('suggested', 'approved', 'overridden')",
            name="valid_intelligence_category_status",
        ),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["suggested_category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),
    )
    op.create_index(op.f("ix_document_intelligence_document_id"), "document_intelligence", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_intelligence_suggested_category_id"), "document_intelligence", ["suggested_category_id"], unique=False)
    op.create_index(op.f("ix_document_intelligence_category_status"), "document_intelligence", ["category_status"], unique=False)

    op.create_table(
        "document_review_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("resolved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint(
            "review_type IN ('low_confidence', 'uncategorized', 'missing_tags', 'duplicates', 'action_items', 'processing_issues')",
            name="valid_review_item_type",
        ),
        sa.CheckConstraint("status IN ('open', 'resolved', 'dismissed')", name="valid_review_item_status"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_document_review_items_document_id"), "document_review_items", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_review_items_review_type"), "document_review_items", ["review_type"], unique=False)
    op.create_index(op.f("ix_document_review_items_status"), "document_review_items", ["status"], unique=False)
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_document_review_items_open
        ON document_review_items (document_id, review_type)
        WHERE status = 'open'
        """
    )

    op.create_table(
        "document_action_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("source", sa.String(length=20), nullable=False, server_default="ai"),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("dismissed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("state IN ('open', 'completed', 'dismissed')", name="valid_action_item_state"),
        sa.CheckConstraint("source IN ('ai', 'user')", name="valid_action_item_source"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "content", name="unique_document_action_item_content"),
    )
    op.create_index(op.f("ix_document_action_items_document_id"), "document_action_items", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_action_items_state"), "document_action_items", ["state"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_document_action_items_state"), table_name="document_action_items")
    op.drop_index(op.f("ix_document_action_items_document_id"), table_name="document_action_items")
    op.drop_table("document_action_items")

    op.execute("DROP INDEX IF EXISTS ux_document_review_items_open")
    op.drop_index(op.f("ix_document_review_items_status"), table_name="document_review_items")
    op.drop_index(op.f("ix_document_review_items_review_type"), table_name="document_review_items")
    op.drop_index(op.f("ix_document_review_items_document_id"), table_name="document_review_items")
    op.drop_table("document_review_items")

    op.drop_index(op.f("ix_document_intelligence_category_status"), table_name="document_intelligence")
    op.drop_index(op.f("ix_document_intelligence_suggested_category_id"), table_name="document_intelligence")
    op.drop_index(op.f("ix_document_intelligence_document_id"), table_name="document_intelligence")
    op.drop_table("document_intelligence")

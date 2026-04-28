"""add dedicated document relationship review workflow

Revision ID: 20260428_0009
Revises: 20260428_0008
Create Date: 2026-04-28 06:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260428_0009"
down_revision: Union[str, None] = "20260428_0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_relationship_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("reason_codes_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.CheckConstraint("source_document_id != target_document_id", name="no_self_relationship_review"),
        sa.CheckConstraint(
            "relationship_type IN ('duplicate', 'similar', 'related')",
            name="valid_relationship_review_type",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'confirmed', 'dismissed')",
            name="valid_relationship_review_status",
        ),
        sa.CheckConstraint(
            "confidence IS NULL OR (confidence >= 0 AND confidence <= 1)",
            name="valid_relationship_review_confidence",
        ),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_document_relationship_reviews_source_document_id"),
        "document_relationship_reviews",
        ["source_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_relationship_reviews_target_document_id"),
        "document_relationship_reviews",
        ["target_document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_relationship_reviews_relationship_type"),
        "document_relationship_reviews",
        ["relationship_type"],
        unique=False,
    )
    op.create_index(op.f("ix_document_relationship_reviews_status"), "document_relationship_reviews", ["status"], unique=False)
    op.create_index(op.f("ix_document_relationship_reviews_reviewed_by"), "document_relationship_reviews", ["reviewed_by"], unique=False)

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS ux_document_relationship_reviews_pending
        ON document_relationship_reviews (source_document_id, target_document_id, relationship_type)
        WHERE status = 'pending'
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ux_document_relationship_reviews_pending")
    op.drop_index(op.f("ix_document_relationship_reviews_reviewed_by"), table_name="document_relationship_reviews")
    op.drop_index(op.f("ix_document_relationship_reviews_status"), table_name="document_relationship_reviews")
    op.drop_index(op.f("ix_document_relationship_reviews_relationship_type"), table_name="document_relationship_reviews")
    op.drop_index(op.f("ix_document_relationship_reviews_target_document_id"), table_name="document_relationship_reviews")
    op.drop_index(op.f("ix_document_relationship_reviews_source_document_id"), table_name="document_relationship_reviews")
    op.drop_table("document_relationship_reviews")

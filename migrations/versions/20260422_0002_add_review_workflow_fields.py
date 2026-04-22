"""add review workflow fields

Revision ID: 20260422_0002
Revises: 20260422_0001
Create Date: 2026-04-22 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260422_0002"
down_revision: Union[str, None] = "20260422_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("review_status", sa.String(length=50), nullable=False, server_default="pending"))
    op.add_column("documents", sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("documents", sa.Column("reviewed_by", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("override_summary", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("override_tags", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index(op.f("ix_documents_review_status"), "documents", ["review_status"], unique=False)
    op.create_check_constraint(
        "valid_review_status",
        "documents",
        "review_status IN ('pending', 'approved', 'rejected', 'edited')",
    )
    op.alter_column("documents", "review_status", server_default=None)


def downgrade() -> None:
    op.drop_constraint("valid_review_status", "documents", type_="check")
    op.drop_index(op.f("ix_documents_review_status"), table_name="documents")
    op.drop_column("documents", "override_tags")
    op.drop_column("documents", "override_summary")
    op.drop_column("documents", "reviewed_by")
    op.drop_column("documents", "reviewed_at")
    op.drop_column("documents", "review_status")

"""add gmail imported attachments

Revision ID: 20260430_0014
Revises: 20260430_0013
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260430_0014"
down_revision = "20260430_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "gmail_imported_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gmail_message_id", sa.String(length=255), nullable=False),
        sa.Column("attachment_id", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=255)),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "gmail_message_id", "attachment_id", name="uq_gmail_imported_attachment_per_user"),
    )


def downgrade() -> None:
    op.drop_table("gmail_imported_attachments")

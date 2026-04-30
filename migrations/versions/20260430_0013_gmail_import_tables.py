"""gmail import tables

Revision ID: 20260430_0013
Revises: 20260430_0012
Create Date: 2026-04-30
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260430_0013"
down_revision = "20260430_0012"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("gmail_import_rules", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("sender_email", sa.String(length=255), nullable=False), sa.Column("query", sa.String(length=255)), sa.Column("include_attachments", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("max_results", sa.Integer(), nullable=False, server_default="20"), sa.Column("last_imported_at", sa.TIMESTAMP(timezone=True)), sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False), sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"],["users.id"], ondelete="CASCADE"))
    op.create_table("gmail_imported_messages", sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True), sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("gmail_message_id", sa.String(length=255), nullable=False), sa.Column("gmail_thread_id", sa.String(length=255)), sa.Column("sender", sa.String(length=255)), sa.Column("subject", sa.String(length=255)), sa.Column("received_at", sa.TIMESTAMP(timezone=True)), sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False), sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False), sa.ForeignKeyConstraint(["user_id"],["users.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["document_id"],["documents.id"], ondelete="CASCADE"), sa.UniqueConstraint("user_id","gmail_message_id", name="uq_gmail_imported_message_per_user"))

def downgrade() -> None:
    op.drop_table("gmail_imported_messages")
    op.drop_table("gmail_import_rules")

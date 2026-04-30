"""chatbot and reports

Revision ID: 20260430_0012
Revises: 20260430_0011
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260430_0012"
down_revision = "20260430_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chatbot_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("retrieval_prompt", sa.Text(), nullable=False),
        sa.Column("report_prompt", sa.Text(), nullable=False),
        sa.Column("citation_prompt", sa.Text(), nullable=False),
        sa.Column("default_report_template", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("max_tokens", sa.Integer(), nullable=False),
        sa.Column("max_documents", sa.Integer(), nullable=False),
        sa.Column("allow_full_text_retrieval", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "generated_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("source_document_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

def downgrade() -> None:
    op.drop_table("generated_reports")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("chatbot_settings")

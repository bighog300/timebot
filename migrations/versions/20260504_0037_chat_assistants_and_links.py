"""chat assistants and links

Revision ID: 20260504_0037
Revises: 20260504_0036
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260504_0037"
down_revision = "20260504_0036"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "assistant_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_plan", sa.String(length=50), nullable=False, server_default="free"),
        sa.Column("default_prompt_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["default_prompt_template_id"], ["prompt_templates.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "chat_document_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_chat_document_links_document_id"), "chat_document_links", ["document_id"], unique=False)
    op.create_index(op.f("ix_chat_document_links_session_id"), "chat_document_links", ["session_id"], unique=False)

    op.add_column("chat_sessions", sa.Column("assistant_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("chat_sessions", sa.Column("prompt_template_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("chat_sessions", sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("chat_sessions", sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_foreign_key(None, "chat_sessions", "assistant_profiles", ["assistant_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(None, "chat_sessions", "prompt_templates", ["prompt_template_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_chat_sessions_assistant_id"), "chat_sessions", ["assistant_id"], unique=False)
    op.create_index(op.f("ix_chat_sessions_prompt_template_id"), "chat_sessions", ["prompt_template_id"], unique=False)

    op.add_column(
        "chat_messages",
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )

    op.alter_column("chat_sessions", "is_archived", server_default=None)
    op.alter_column("chat_sessions", "is_deleted", server_default=None)
    op.alter_column("chat_messages", "metadata_json", server_default=None)


def downgrade() -> None:
    op.drop_column("chat_messages", "metadata_json")
    op.drop_index(op.f("ix_chat_sessions_prompt_template_id"), table_name="chat_sessions")
    op.drop_index(op.f("ix_chat_sessions_assistant_id"), table_name="chat_sessions")
    op.drop_constraint(None, "chat_sessions", type_="foreignkey")
    op.drop_constraint(None, "chat_sessions", type_="foreignkey")
    op.drop_column("chat_sessions", "is_deleted")
    op.drop_column("chat_sessions", "is_archived")
    op.drop_column("chat_sessions", "prompt_template_id")
    op.drop_column("chat_sessions", "assistant_id")
    op.drop_index(op.f("ix_chat_document_links_session_id"), table_name="chat_document_links")
    op.drop_index(op.f("ix_chat_document_links_document_id"), table_name="chat_document_links")
    op.drop_table("chat_document_links")
    op.drop_table("assistant_profiles")

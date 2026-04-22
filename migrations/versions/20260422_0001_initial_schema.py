"""initial schema

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260422_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=True),
        sa.Column("created_by_user", sa.Boolean(), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=True),
        sa.Column("last_used", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_categories_ai_generated"), "categories", ["ai_generated"], unique=False)
    op.create_index(op.f("ix_categories_document_count"), "categories", ["document_count"], unique=False)
    op.create_index(op.f("ix_categories_name"), "categories", ["name"], unique=False)
    op.create_index(op.f("ix_categories_slug"), "categories", ["slug"], unique=False)

    op.create_table(
        "connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("last_sync_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(length=50), nullable=True),
        sa.Column("sync_progress", sa.Integer(), nullable=True),
        sa.Column("document_count", sa.Integer(), nullable=True),
        sa.Column("total_size", sa.BigInteger(), nullable=True),
        sa.Column("auto_sync", sa.Boolean(), nullable=True),
        sa.Column("sync_interval", sa.Integer(), nullable=True),
        sa.Column("is_authenticated", sa.Boolean(), nullable=True),
        sa.Column("token_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("sync_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("last_sync_status IS NULL OR last_sync_status IN ('success', 'failed', 'partial', 'in_progress')", name="valid_sync_status"),
        sa.CheckConstraint("status IN ('connected', 'disconnected', 'error', 'syncing')", name="valid_connection_status"),
        sa.CheckConstraint("sync_progress >= 0 AND sync_progress <= 100", name="valid_sync_progress"),
        sa.CheckConstraint("type IN ('gmail', 'gdrive', 'dropbox', 'onedrive')", name="valid_connection_type"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type", name="unique_connection_type"),
    )
    op.create_index(op.f("ix_connections_last_sync_date"), "connections", ["last_sync_date"], unique=False)
    op.create_index(op.f("ix_connections_status"), "connections", ["status"], unique=False)
    op.create_index(op.f("ix_connections_type"), "connections", ["type"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_path", sa.Text(), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column("upload_date", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("last_modified", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("processed_date", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("key_points", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("entities", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("action_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ai_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("user_category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ai_tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("user_tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("extracted_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("processing_status", sa.String(length=50), nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=True),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_favorite", sa.Boolean(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=True),
        sa.Column("user_notes", sa.Text(), nullable=True),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)", name="valid_confidence"),
        sa.CheckConstraint("processing_status IN ('pending', 'queued', 'processing', 'completed', 'failed')", name="valid_processing_status"),
        sa.CheckConstraint("source IN ('upload', 'gmail', 'gdrive', 'dropbox', 'onedrive')", name="valid_source"),
        sa.ForeignKeyConstraint(["ai_category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_documents_ai_category_id"), "documents", ["ai_category_id"], unique=False)
    op.create_index(op.f("ix_documents_connection_id"), "documents", ["connection_id"], unique=False)
    op.create_index(op.f("ix_documents_file_type"), "documents", ["file_type"], unique=False)
    op.create_index(op.f("ix_documents_filename"), "documents", ["filename"], unique=False)
    op.create_index(op.f("ix_documents_is_archived"), "documents", ["is_archived"], unique=False)
    op.create_index(op.f("ix_documents_is_favorite"), "documents", ["is_favorite"], unique=False)
    op.create_index(op.f("ix_documents_processing_status"), "documents", ["processing_status"], unique=False)
    op.create_index(op.f("ix_documents_source"), "documents", ["source"], unique=False)
    op.create_index(op.f("ix_documents_upload_date"), "documents", ["upload_date"], unique=False)
    op.create_index(op.f("ix_documents_user_category_id"), "documents", ["user_category_id"], unique=False)

    op.create_table(
        "document_relationships",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_doc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_doc_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="valid_relationship_confidence"),
        sa.CheckConstraint("relationship_type IN ('similar_to', 'references', 'follows_up', 'related_to', 'duplicates')", name="valid_relationship_type"),
        sa.CheckConstraint("source_doc_id != target_doc_id", name="no_self_reference"),
        sa.ForeignKeyConstraint(["source_doc_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_doc_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_doc_id", "target_doc_id", "relationship_type", name="unique_relationship"),
    )
    op.create_index(op.f("ix_document_relationships_relationship_type"), "document_relationships", ["relationship_type"], unique=False)
    op.create_index(op.f("ix_document_relationships_source_doc_id"), "document_relationships", ["source_doc_id"], unique=False)
    op.create_index(op.f("ix_document_relationships_target_doc_id"), "document_relationships", ["target_doc_id"], unique=False)

    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("changed_fields", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("changed_by", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("changed_by IS NULL OR changed_by IN ('user', 'ai', 'sync')", name="valid_changed_by"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "version_number", name="unique_document_version"),
    )
    op.create_index(op.f("ix_document_versions_created_at"), "document_versions", ["created_at"], unique=False)
    op.create_index(op.f("ix_document_versions_document_id"), "document_versions", ["document_id"], unique=False)

    op.create_table(
        "processing_queue",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_type", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("priority >= 1 AND priority <= 10", name="valid_priority"),
        sa.CheckConstraint("status IN ('queued', 'processing', 'completed', 'failed')", name="valid_queue_status"),
        sa.CheckConstraint("task_type IN ('extract_text', 'ai_analysis', 'generate_thumbnail', 'embed_document', 'detect_relationships')", name="valid_task_type"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "task_type", name="unique_document_task"),
    )
    op.create_index(op.f("ix_processing_queue_document_id"), "processing_queue", ["document_id"], unique=False)
    op.create_index(op.f("ix_processing_queue_priority"), "processing_queue", ["priority"], unique=False)
    op.create_index(op.f("ix_processing_queue_status"), "processing_queue", ["status"], unique=False)
    op.create_index(op.f("ix_processing_queue_task_type"), "processing_queue", ["task_type"], unique=False)

    op.create_table(
        "sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=True),
        sa.Column("documents_added", sa.Integer(), nullable=True),
        sa.Column("documents_updated", sa.Integer(), nullable=True),
        sa.Column("documents_failed", sa.Integer(), nullable=True),
        sa.Column("bytes_synced", sa.BigInteger(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('success', 'failed', 'partial', 'in_progress')", name="valid_sync_log_status"),
        sa.ForeignKeyConstraint(["connection_id"], ["connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sync_logs_connection_id"), "sync_logs", ["connection_id"], unique=False)
    op.create_index(op.f("ix_sync_logs_start_time"), "sync_logs", ["start_time"], unique=False)
    op.create_index(op.f("ix_sync_logs_status"), "sync_logs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sync_logs_status"), table_name="sync_logs")
    op.drop_index(op.f("ix_sync_logs_start_time"), table_name="sync_logs")
    op.drop_index(op.f("ix_sync_logs_connection_id"), table_name="sync_logs")
    op.drop_table("sync_logs")

    op.drop_index(op.f("ix_processing_queue_task_type"), table_name="processing_queue")
    op.drop_index(op.f("ix_processing_queue_status"), table_name="processing_queue")
    op.drop_index(op.f("ix_processing_queue_priority"), table_name="processing_queue")
    op.drop_index(op.f("ix_processing_queue_document_id"), table_name="processing_queue")
    op.drop_table("processing_queue")

    op.drop_index(op.f("ix_document_versions_document_id"), table_name="document_versions")
    op.drop_index(op.f("ix_document_versions_created_at"), table_name="document_versions")
    op.drop_table("document_versions")

    op.drop_index(op.f("ix_document_relationships_target_doc_id"), table_name="document_relationships")
    op.drop_index(op.f("ix_document_relationships_source_doc_id"), table_name="document_relationships")
    op.drop_index(op.f("ix_document_relationships_relationship_type"), table_name="document_relationships")
    op.drop_table("document_relationships")

    op.drop_index(op.f("ix_documents_user_category_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_upload_date"), table_name="documents")
    op.drop_index(op.f("ix_documents_source"), table_name="documents")
    op.drop_index(op.f("ix_documents_processing_status"), table_name="documents")
    op.drop_index(op.f("ix_documents_is_favorite"), table_name="documents")
    op.drop_index(op.f("ix_documents_is_archived"), table_name="documents")
    op.drop_index(op.f("ix_documents_filename"), table_name="documents")
    op.drop_index(op.f("ix_documents_file_type"), table_name="documents")
    op.drop_index(op.f("ix_documents_connection_id"), table_name="documents")
    op.drop_index(op.f("ix_documents_ai_category_id"), table_name="documents")
    op.drop_table("documents")

    op.drop_index(op.f("ix_connections_type"), table_name="connections")
    op.drop_index(op.f("ix_connections_status"), table_name="connections")
    op.drop_index(op.f("ix_connections_last_sync_date"), table_name="connections")
    op.drop_table("connections")

    op.drop_index(op.f("ix_categories_slug"), table_name="categories")
    op.drop_index(op.f("ix_categories_name"), table_name="categories")
    op.drop_index(op.f("ix_categories_document_count"), table_name="categories")
    op.drop_index(op.f("ix_categories_ai_generated"), table_name="categories")
    op.drop_table("categories")

"""add source mapping phase2 tables

Revision ID: 20260428_0005
Revises: 20260422_0004
Create Date: 2026-04-28 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260428_0005"
down_revision: Union[str, None] = "20260422_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "source_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("profile_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_source_profiles_source_id"), "source_profiles", ["source_id"], unique=False)
    op.create_index(op.f("ix_source_profiles_status"), "source_profiles", ["status"], unique=False)

    op.create_table(
        "url_families",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("family_key", sa.String(length=255), nullable=False),
        sa.Column("sample_url", sa.Text(), nullable=False),
        sa.Column("locator_hint", sa.String(length=255), nullable=True),
        sa.Column("suggestion", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("family_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_profile_id"], ["source_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_url_families_source_profile_id"), "url_families", ["source_profile_id"], unique=False)

    op.create_table(
        "mapping_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("source_profile_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_profile_id"], ["source_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_mapping_drafts_source_id"), "mapping_drafts", ["source_id"], unique=False)
    op.create_index(op.f("ix_mapping_drafts_source_profile_id"), "mapping_drafts", ["source_profile_id"], unique=False)
    op.create_index(op.f("ix_mapping_drafts_status"), "mapping_drafts", ["status"], unique=False)

    op.create_table(
        "mapping_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("draft_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("rule_order", sa.Integer(), nullable=False),
        sa.Column("family_key", sa.String(length=255), nullable=False),
        sa.Column("sample_url", sa.Text(), nullable=False),
        sa.Column("selector_suggestion", sa.String(length=255), nullable=True),
        sa.Column("parse_suggestion", sa.String(length=255), nullable=True),
        sa.Column("transform_suggestion", sa.String(length=255), nullable=True),
        sa.Column("selector_override", sa.String(length=255), nullable=True),
        sa.Column("parse_override", sa.String(length=255), nullable=True),
        sa.Column("transform_override", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["mapping_drafts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("draft_id", "family_key", name="uq_mapping_rules_draft_family"),
    )
    op.create_index(op.f("ix_mapping_rules_draft_id"), "mapping_rules", ["draft_id"], unique=False)
    op.create_index(op.f("ix_mapping_rules_source_id"), "mapping_rules", ["source_id"], unique=False)

    op.create_table(
        "active_source_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", sa.String(length=255), nullable=False),
        sa.Column("mapping_draft_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("compiled_mapping", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("activated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("activated_by", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["mapping_draft_id"], ["mapping_drafts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id"),
    )
    op.create_index(op.f("ix_active_source_mappings_source_id"), "active_source_mappings", ["source_id"], unique=True)
    op.create_index(op.f("ix_active_source_mappings_mapping_draft_id"), "active_source_mappings", ["mapping_draft_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_active_source_mappings_mapping_draft_id"), table_name="active_source_mappings")
    op.drop_index(op.f("ix_active_source_mappings_source_id"), table_name="active_source_mappings")
    op.drop_table("active_source_mappings")

    op.drop_index(op.f("ix_mapping_rules_source_id"), table_name="mapping_rules")
    op.drop_index(op.f("ix_mapping_rules_draft_id"), table_name="mapping_rules")
    op.drop_table("mapping_rules")

    op.drop_index(op.f("ix_mapping_drafts_status"), table_name="mapping_drafts")
    op.drop_index(op.f("ix_mapping_drafts_source_profile_id"), table_name="mapping_drafts")
    op.drop_index(op.f("ix_mapping_drafts_source_id"), table_name="mapping_drafts")
    op.drop_table("mapping_drafts")

    op.drop_index(op.f("ix_url_families_source_profile_id"), table_name="url_families")
    op.drop_table("url_families")

    op.drop_index(op.f("ix_source_profiles_status"), table_name="source_profiles")
    op.drop_index(op.f("ix_source_profiles_source_id"), table_name="source_profiles")
    op.drop_table("source_profiles")

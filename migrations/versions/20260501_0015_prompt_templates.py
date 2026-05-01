"""add prompt templates table

Revision ID: 20260501_0015
Revises: 20260430_0014
Create Date: 2026-05-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260501_0015"
down_revision = "20260430_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type", "name", "version", name="uq_prompt_templates_type_name_version"),
    )
    op.create_index("ix_prompt_templates_type", "prompt_templates", ["type"], unique=False)
    op.create_index("ix_prompt_templates_is_active", "prompt_templates", ["is_active"], unique=False)
    op.create_index(
        "ix_prompt_templates_type_active_updated",
        "prompt_templates",
        ["type", "is_active", "updated_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_prompt_templates_type_active_updated", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_is_active", table_name="prompt_templates")
    op.drop_index("ix_prompt_templates_type", table_name="prompt_templates")
    op.drop_table("prompt_templates")

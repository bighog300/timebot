"""email campaign safety phase e4

Revision ID: 20260503_0033
Revises: 20260503_0032
Create Date: 2026-05-03 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260503_0033"
down_revision = "20260503_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_suppressions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=True),
        sa.Column("created_by_admin_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_email_suppressions_email"), "email_suppressions", ["email"], unique=False)

    op.create_table(
        "email_campaign_recipients",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("skip_reason", sa.String(length=255), nullable=True),
        sa.Column("send_log_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("failed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["email_campaigns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["send_log_id"], ["email_send_logs.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_email_campaign_recipients_campaign_id"), "email_campaign_recipients", ["campaign_id"], unique=False)
    op.create_index(op.f("ix_email_campaign_recipients_email"), "email_campaign_recipients", ["email"], unique=False)
    op.create_index(op.f("ix_email_campaign_recipients_status"), "email_campaign_recipients", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_email_campaign_recipients_status"), table_name="email_campaign_recipients")
    op.drop_index(op.f("ix_email_campaign_recipients_email"), table_name="email_campaign_recipients")
    op.drop_index(op.f("ix_email_campaign_recipients_campaign_id"), table_name="email_campaign_recipients")
    op.drop_table("email_campaign_recipients")
    op.drop_index(op.f("ix_email_suppressions_email"), table_name="email_suppressions")
    op.drop_table("email_suppressions")

"""add user plan and usage counters

Revision ID: 20260501_0017
Revises: 20260501_0016
Create Date: 2026-05-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260501_0017"
down_revision = "20260501_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("plan", sa.String(length=20), nullable=False, server_default="free"))
    op.add_column("users", sa.Column("documents_uploaded_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("reports_generated_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("chat_messages_count", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("users", "chat_messages_count")
    op.drop_column("users", "reports_generated_count")
    op.drop_column("users", "documents_uploaded_count")
    op.drop_column("users", "plan")

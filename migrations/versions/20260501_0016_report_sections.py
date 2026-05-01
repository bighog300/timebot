"""add report sections jsonb

Revision ID: 20260501_0016
Revises: 20260501_0015
Create Date: 2026-05-01 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260501_0016"
down_revision = "20260501_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("generated_reports", sa.Column("sections", postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column("generated_reports", "sections")

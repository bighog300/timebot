"""safety add legacy user billing columns if missing

Revision ID: 20260504_0038
Revises: 20260504_0037
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa

revision = "20260504_0038"
down_revision = "20260504_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = {c["name"] for c in inspector.get_columns("users")}

    if "subscription_status" not in cols:
        op.add_column("users", sa.Column("subscription_status", sa.String(length=20), nullable=False, server_default="none"))
        op.alter_column("users", "subscription_status", server_default=None)

    if "plan_started_at" not in cols:
        op.add_column("users", sa.Column("plan_started_at", sa.TIMESTAMP(timezone=True), nullable=True))

    if "plan_expires_at" not in cols:
        op.add_column("users", sa.Column("plan_expires_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    # no-op: safety migration should not remove potentially required legacy columns
    pass

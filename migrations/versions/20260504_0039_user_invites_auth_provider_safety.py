"""safety add missing user_invites auth fields

Revision ID: 20260504_0039
Revises: 20260504_0038
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa

revision = "20260504_0039"
down_revision = "20260504_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "user_invites" not in tables:
        return

    cols = {c["name"] for c in inspector.get_columns("user_invites")}

    if "auth_provider" not in cols:
        op.add_column(
            "user_invites",
            sa.Column("auth_provider", sa.String(length=32), nullable=False, server_default="local"),
        )
        op.alter_column("user_invites", "auth_provider", server_default=None)

    if "google_subject" not in cols:
        op.add_column("user_invites", sa.Column("google_subject", sa.String(length=255), nullable=True))


def downgrade() -> None:
    # no-op: safety migration should not remove columns from upgraded databases
    pass

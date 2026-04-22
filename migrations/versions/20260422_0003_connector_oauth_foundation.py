"""connector oauth foundation

Revision ID: 20260422_0003
Revises: 20260422_0002
Create Date: 2026-04-22 01:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260422_0003"
down_revision: Union[str, None] = "20260422_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("connections", sa.Column("external_account_id", sa.String(length=255), nullable=True))
    op.add_column("connections", sa.Column("access_token", sa.Text(), nullable=True))
    op.add_column("connections", sa.Column("refresh_token", sa.Text(), nullable=True))
    op.add_column("connections", sa.Column("token_scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("connections", sa.Column("oauth_state", sa.String(length=255), nullable=True))
    op.add_column("connections", sa.Column("oauth_state_expires_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("connections", sa.Column("last_error_message", sa.Text(), nullable=True))
    op.add_column("connections", sa.Column("last_error_at", sa.TIMESTAMP(timezone=True), nullable=True))

    op.execute(
        "UPDATE connections SET token_scopes = '[]'::jsonb WHERE token_scopes IS NULL"
    )

    op.drop_constraint("valid_connection_status", "connections", type_="check")
    op.create_check_constraint(
        "valid_connection_status",
        "connections",
        "status IN ('connected', 'disconnected', 'error', 'syncing', 'auth_pending')",
    )


def downgrade() -> None:
    op.drop_constraint("valid_connection_status", "connections", type_="check")
    op.create_check_constraint(
        "valid_connection_status",
        "connections",
        "status IN ('connected', 'disconnected', 'error', 'syncing')",
    )

    op.drop_column("connections", "last_error_at")
    op.drop_column("connections", "last_error_message")
    op.drop_column("connections", "oauth_state_expires_at")
    op.drop_column("connections", "oauth_state")
    op.drop_column("connections", "token_scopes")
    op.drop_column("connections", "refresh_token")
    op.drop_column("connections", "access_token")
    op.drop_column("connections", "external_account_id")

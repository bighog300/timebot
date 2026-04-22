"""app auth users and ownership scoping

Revision ID: 20260422_0004
Revises: 20260422_0003
Create Date: 2026-04-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260422_0004"
down_revision: Union[str, None] = "20260422_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column("documents", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_documents_user_id", "documents", ["user_id"], unique=False)
    op.create_foreign_key("fk_documents_user_id", "documents", "users", ["user_id"], ["id"], ondelete="SET NULL")

    op.add_column("connections", sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_connections_user_id", "connections", ["user_id"], unique=False)
    op.create_foreign_key("fk_connections_user_id", "connections", "users", ["user_id"], ["id"], ondelete="CASCADE")

    op.drop_constraint("unique_connection_type", "connections", type_="unique")
    op.create_unique_constraint("unique_connection_per_user", "connections", ["user_id", "type"])


def downgrade() -> None:
    op.drop_constraint("unique_connection_per_user", "connections", type_="unique")
    op.create_unique_constraint("unique_connection_type", "connections", ["type"])

    op.drop_constraint("fk_connections_user_id", "connections", type_="foreignkey")
    op.drop_index("ix_connections_user_id", table_name="connections")
    op.drop_column("connections", "user_id")

    op.drop_constraint("fk_documents_user_id", "documents", type_="foreignkey")
    op.drop_index("ix_documents_user_id", table_name="documents")
    op.drop_column("documents", "user_id")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

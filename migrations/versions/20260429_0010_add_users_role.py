"""add users.role column

Revision ID: 20260429_0010
Revises: 20260428_0009
Create Date: 2026-04-29 00:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260429_0010"
down_revision: Union[str, None] = "20260428_0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ROLE_CHECK_NAME = "ck_users_role_valid"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20), nullable=False, server_default="viewer"),
    )
    op.create_check_constraint(ROLE_CHECK_NAME, "users", "role IN ('admin', 'editor', 'viewer')")


def downgrade() -> None:
    op.drop_constraint(ROLE_CHECK_NAME, "users", type_="check")
    op.drop_column("users", "role")

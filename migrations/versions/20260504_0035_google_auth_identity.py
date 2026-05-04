"""google auth identity fields

Revision ID: 20260504_0035
Revises: 20260504_0034, 20260504_0034_sim_rec_mod
Create Date: 2026-05-04 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "20260504_0035"
down_revision = ("20260504_0034", "20260504_0034_sim_rec_mod")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("auth_provider", sa.String(length=20), nullable=False, server_default="local"))
    op.add_column("users", sa.Column("google_subject", sa.String(length=255), nullable=True))
    op.create_unique_constraint("uq_users_google_subject", "users", ["google_subject"])


def downgrade() -> None:
    op.drop_constraint("uq_users_google_subject", "users", type_="unique")
    op.drop_column("users", "google_subject")
    op.drop_column("users", "auth_provider")

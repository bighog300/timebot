"""remove source mapping and crawler-adjacent tables

Revision ID: 20260428_0006
Revises: 20260422_0004
Create Date: 2026-04-28 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260428_0006"
down_revision: Union[str, None] = "20260422_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS active_source_mappings CASCADE")
    op.execute("DROP TABLE IF EXISTS mapping_rules CASCADE")
    op.execute("DROP TABLE IF EXISTS mapping_drafts CASCADE")
    op.execute("DROP TABLE IF EXISTS url_families CASCADE")
    op.execute("DROP TABLE IF EXISTS source_profiles CASCADE")


def downgrade() -> None:
    # Source mapping/crawler table support was removed from the product.
    # Downgrade intentionally does not recreate retired tables.
    pass

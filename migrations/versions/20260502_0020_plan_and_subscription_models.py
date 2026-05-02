"""add plan and subscription models

Revision ID: 20260502_0020
Revises: 20260502_0019
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
import uuid
from sqlalchemy.dialects import postgresql

revision = "20260502_0020"
down_revision = "20260502_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("price_monthly_cents", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="usd"),
        sa.Column("limits_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("features_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_plans_slug", "plans", ["slug"], unique=True)

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("current_period_start", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("current_period_end", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("external_provider", sa.String(length=50), nullable=True),
        sa.Column("external_customer_id", sa.String(length=255), nullable=True),
        sa.Column("external_subscription_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_subscriptions_user_id", "subscriptions", ["user_id"], unique=False)
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"], unique=False)

    plans_table = sa.table(
        "plans",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("slug", sa.String(length=50)),
        sa.column("name", sa.String(length=100)),
        sa.column("price_monthly_cents", sa.Integer()),
        sa.column("currency", sa.String(length=10)),
        sa.column("limits_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.column("features_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        plans_table,
        [
            {
                "id": uuid.uuid4(),
                "slug": "free",
                "name": "Free",
                "price_monthly_cents": 0,
                "currency": "usd",
                "limits_json": {"documents": 25, "reports": 10, "chat_messages": 200},
                "features_json": {"basic_search": True, "chat": True},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "pro",
                "name": "Pro",
                "price_monthly_cents": 2900,
                "currency": "usd",
                "limits_json": {"documents": None, "reports": None, "chat_messages": None},
                "features_json": {"basic_search": True, "chat": True, "priority_support": True},
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "slug": "team",
                "name": "Team",
                "price_monthly_cents": 9900,
                "currency": "usd",
                "limits_json": {"documents": None, "reports": None, "chat_messages": None, "seats": 10},
                "features_json": {"basic_search": True, "chat": True, "priority_support": True, "team_workspace": True},
                "is_active": True,
            },
        ],
    )



def downgrade() -> None:
    op.drop_index("ix_subscriptions_plan_id", table_name="subscriptions")
    op.drop_index("ix_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("ix_plans_slug", table_name="plans")
    op.drop_table("plans")

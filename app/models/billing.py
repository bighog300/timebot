import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    price_monthly_cents = Column(Integer, nullable=False)
    currency = Column(String(10), nullable=False, default="usd")
    limits_json = Column(JSONB, nullable=False, default=dict)
    features_json = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True)
    status = Column(String(30), nullable=False, default="active")
    current_period_start = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    current_period_end = Column(TIMESTAMP(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, nullable=False, default=False)
    external_provider = Column(String(50), nullable=True)
    usage_credits_json = Column(JSONB, nullable=False, default=dict)
    limit_overrides_json = Column(JSONB, nullable=False, default=dict)
    external_customer_id = Column(String(255), nullable=True)
    external_subscription_id = Column(String(255), nullable=True)
    billing_customer_id = Column(String(255), nullable=True)
    billing_subscription_id = Column(String(255), nullable=True)
    billing_price_id = Column(String(255), nullable=True)
    billing_provider = Column(String(50), nullable=True)
    billing_current_period_end = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")
